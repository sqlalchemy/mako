from mako.util import LRUCache
import string, unittest, time, random

import thread

class item:
    def __init__(self, id):
        self.id = id

    def __str__(self):
        return "item id %d" % self.id

class LRUTest(unittest.TestCase):


    def testlru(self):                
        l = LRUCache(10, threshold=.2)
        
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

    def disabled_test_threaded(self):
        size = 100
        threshold = .5
        all_elems = 2000
        hot_zone = range(30,100)
        cache = LRUCache(size, threshold)
        class Element(object):
            def __init__(self, id):
                self.id = id
        def get_elem():
            if random.randint(1,4) == 1:
                return hot_zone[random.randint(0, len(hot_zone) - 1)]
            else:
                return random.randint(1, all_elems)
        
        def request_elem():
            while True:
                id = get_elem()
                try:
                    elem = cache[id]
                except KeyError:
                    cache[id] = Element(id)
                time.sleep(random.random() / 1000)
        for x in range(0,20):
            thread.start_new_thread(request_elem, ())
        for x in range(0,5):
            time.sleep(1)
            #print "size:", len(cache)
            assert len(cache) < size + size * threshold * 2
            assert len(cache) > size - (size * .1)
        total = 0
        for h in hot_zone:
            if h in cache:
                total += 1
        #print "total hot zone in cache: " , total, "of", len(hot_zone)
        
if __name__ == "__main__":
    unittest.main()
