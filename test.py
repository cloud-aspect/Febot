import wrapt
from decorator import decorator

class A:
    def init(self, b):
        b.add(self.hai())


    def hai(self):
        print('hai')


class B:
    def add(self, a):
        self.a = a

    def run(self):
        self.a()
    
class C(A):
    def hai(self):
        print('hey')

b = B()
c = C(b)


print(b.run())