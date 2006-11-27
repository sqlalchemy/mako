from mako.util import LRUCache
import string, unittest, time

class item:
    def __init__(self, id):
        self.id = id

    def __str__(self):
        return "item id %d" % self.id

class LRUTest(unittest.TestCase):

    def setUp(self):
        self.cache = LRUCache(10, threshold=.2)

    def print_cache(l):
        for item in l:
            print item,
        print    
        

    def testlru(self):                
        l = self.cache
        
        for id in range(1,20):
            time.sleep(.001)
            l[id] = item(id)
        
        # first couple of items should be gone
        self.assert_(not l.has_key(1))    
        self.assert_(not l.has_key(2))
        
        # next batch over the threshold of 10 should be present
        for id in range(11,20):
            self.assert_(l.has_key(id))

        l[12]
        l[15]
        l[23] = item(23)
        l[24] = item(24)
        l[25] = item(25)

        self.assert_(not l.has_key(11))
        self.assert_(not l.has_key(13))
        
        for id in (25, 24, 23, 14, 12, 19, 18, 17, 16, 15):
            self.assert_(l.has_key(id))    


if __name__ == "__main__":
    unittest.main()
