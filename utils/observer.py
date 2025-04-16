from typing import List, Callable, Any

class Observable:
    """可观察对象基类"""
    
    def __init__(self):
        self._observers: List[Callable[[Any], None]] = []
    
    def add_observer(self, observer: Callable[[Any], None]) -> None:
        """添加观察者
        
        Args:
            observer: 观察者回调函数，接收一个参数（通知数据）
        """
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer: Callable[[Any], None]) -> None:
        """移除观察者
        
        Args:
            observer: 要移除的观察者回调函数
        """
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify_observers(self, data: Any = None) -> None:
        """通知所有观察者
        
        Args:
            data: 要传递给观察者的数据
        """
        for observer in self._observers:
            observer(data) 