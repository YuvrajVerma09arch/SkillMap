# app/utils/heap.py

class MaxHeap:
    """
    A manual implementation of a Max Heap (Priority Queue).
    Used to efficiently rank candidates by Match Score.
    """
    def __init__(self):
        self.heap = []

    def push(self, item):
        """
        item: tuple (score, candidate_dict)
        Adds item to heap and maintains max-heap property.
        """
        self.heap.append(item)
        self._heapify_up(len(self.heap) - 1)

    def pop(self):
        """
        Removes and returns the item with the highest score.
        """
        if not self.heap:
            return None
        if len(self.heap) == 1:
            return self.heap.pop()
        
        root = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._heapify_down(0)
        return root

    def _heapify_up(self, index):
        parent_index = (index - 1) // 2
        if index > 0 and self.heap[index][0] > self.heap[parent_index][0]:
            # Swap if current is greater than parent
            self.heap[index], self.heap[parent_index] = self.heap[parent_index], self.heap[index]
            self._heapify_up(parent_index)

    def _heapify_down(self, index):
        largest = index
        left_child = 2 * index + 1
        right_child = 2 * index + 2

        # Check left child
        if left_child < len(self.heap) and self.heap[left_child][0] > self.heap[largest][0]:
            largest = left_child

        # Check right child
        if right_child < len(self.heap) and self.heap[right_child][0] > self.heap[largest][0]:
            largest = right_child

        # Swap if root is not largest
        if largest != index:
            self.heap[index], self.heap[largest] = self.heap[largest], self.heap[index]
            self._heapify_down(largest)
    
    def get_top_n(self, n=5):
        """
        Returns the top N candidates sorted by score.
        """
        result = []
        for _ in range(n):
            item = self.pop()
            if item:
                score, candidate_data = item
                # Add score to data for display
                candidate_data['match_score'] = score
                result.append(candidate_data)
        return result