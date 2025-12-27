"""Progress tracking service using tqdm."""

from tqdm import tqdm
from typing import Iterable, Any


class ProgressService:
    """Progress tracking using tqdm."""
    
    def track(self, items: Iterable[Any], description: str = "Processing"):
        """
        Track progress through an iterable with tqdm progress bar.
        
        Args:
            items: Iterable to track
            description: Description to display
            
        Yields:
            Items from the iterable
        """
        items_list = list(items)
        
        with tqdm(total=len(items_list), desc=description, unit='item') as pbar:
            for item in items_list:
                yield item
                pbar.update(1)
    
    def track_with_status(self, items: Iterable[Any], description: str = "Processing"):
        """
        Track progress with dynamic status updates.
        
        Args:
            items: Iterable to track
            description: Base description
            
        Yields:
            Tuple of (item, updater_function)
        """
        items_list = list(items)
        
        pbar = tqdm(total=len(items_list), desc=description, unit='img')
        
        for item in items_list:
            def update_status(status: str):
                pbar.set_postfix_str(status)
            
            yield item, update_status
            pbar.update(1)
        
        pbar.close()
