import time
from typing import Dict, Optional


class PerformanceTracker:
    """
    Tracks processing performance metrics.
    """
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.total_images = 0
        self.successful_images = 0
        self.failed_images = 0
        self.total_inference_time = 0.0
        self.total_digits_extracted = 0
        self.image_times = []
    
    def start(self):
        """Start timing."""
        self.start_time = time.time()
    
    def record_image(self, success: bool, inference_time: float = 0.0, 
                     digits_extracted: int = 0):
        """
        Record processed image.
        
        Args:
            success: Whether image was processed successfully
            inference_time: Time taken for YOLO inference (seconds)
            digits_extracted: Number of digits successfully extracted
        """
        self.total_images += 1
        if success:
            self.successful_images += 1
        else:
            self.failed_images += 1
        
        self.total_inference_time += inference_time
        self.total_digits_extracted += digits_extracted
        self.image_times.append(inference_time)
    
    def get_metrics(self) -> Dict[str, any]:
        """
        Get current metrics.
        
        Returns:
            Dictionary with metrics
        """
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        avg_time_per_image = (self.total_inference_time / self.total_images 
                             if self.total_images > 0 else 0)
        success_rate = (self.successful_images / self.total_images * 100 
                       if self.total_images > 0 else 0)
        avg_digits_per_image = (self.total_digits_extracted / self.successful_images 
                               if self.successful_images > 0 else 0)
        
        return {
            'total_images': self.total_images,
            'successful_images': self.successful_images,
            'failed_images': self.failed_images,
            'success_rate': success_rate,
            'elapsed_time': elapsed_time,
            'avg_time_per_image': avg_time_per_image,
            'total_inference_time': self.total_inference_time,
            'total_digits_extracted': self.total_digits_extracted,
            'avg_digits_per_image': avg_digits_per_image
        }
    
    def display_metrics(self):
        """Display metrics in formatted output."""
        metrics = self.get_metrics()
        
        print("\n" + "="*60)
        print("⚡ PERFORMANCE METRICS")
        print("="*60)
        print(f"📊 Total Images Processed  : {metrics['total_images']}")
        print(f"✅ Successful              : {metrics['successful_images']}")
        print(f"❌ Failed                  : {metrics['failed_images']}")
        print(f"📈 Success Rate            : {metrics['success_rate']:.1f}%")
        print(f"🔢 Total Digits Extracted  : {metrics['total_digits_extracted']}")
        print(f"📐 Avg Digits per Image    : {metrics['avg_digits_per_image']:.1f}")
        print(f"⏱️  Total Time              : {metrics['elapsed_time']:.2f}s")
        print(f"⚡ Avg Time per Image      : {metrics['avg_time_per_image']:.3f}s")
        print(f"🚀 Avg Inference Time      : {metrics['total_inference_time']/max(1, metrics['total_images']):.3f}s")
        print("="*60 + "\n")
    
    def display_preview_metrics(self, sample_size: int, total_images: int):
        """
        Display preview metrics after benchmark.
        
        Args:
            sample_size: Number of images in benchmark sample
            total_images: Total images to be processed
        """
        metrics = self.get_metrics()
        
        if metrics['total_images'] == 0:
            return
        
        avg_time = metrics['avg_time_per_image']
        estimated_total_time = avg_time * total_images
        
        print("\n" + "="*60)
        print("🔍 PERFORMANCE PREVIEW (Benchmark Results)")
        print("="*60)
        print(f"📊 Sample Size             : {sample_size} images")
        print(f"✅ Successful              : {metrics['successful_images']}/{sample_size}")
        print(f"📈 Success Rate            : {metrics['success_rate']:.1f}%")
        print(f"⚡ Avg Time per Image      : {avg_time:.3f}s")
        print(f"🔢 Avg Digits per Image    : {metrics['avg_digits_per_image']:.1f}")
        print("-" * 60)
        print(f"📦 Total Images to Process : {total_images}")
        print(f"⏱️  Estimated Total Time    : {estimated_total_time:.1f}s ({estimated_total_time/60:.1f} min)")
        print("="*60 + "\n")
    
    def reset(self):
        """Reset all metrics."""
        self.__init__()
