import argparse
import multiprocessing
from multiprocessing.dummy import Pool
from multiprocessing import Manager
import os


class TreeCrawler(object):
    def __init__(self, base_path, callback):
        self.base_path = base_path
        self.unsearched = Manager().Queue()
        self.cpu_count = multiprocessing.cpu_count()
        self.pool = Pool(self.cpu_count)
        # acquire the list of all paths inside base path
        self.first_level_dirs = next(os.walk(self.base_path))[1]

        for path in self.first_level_dirs:
            self.unsearched.put(self.base_path + "/" + path)

    def __explore_path(self, task_num, dirpath):
        directories = []
        print "Task: " + str(task_num) + " >>> Explored path: " + dirpath
        for filename in os.walk(dirpath).next()[1]:
            fullname = os.path.join(dirpath, filename)
            directories.append(fullname)
        return directories

    def run_crawler(self):
        self.pool.map_async(self.parallel_worker, range(self.cpu_count))
        self.pool.close()
        self.unsearched.join()

    def parallel_worker(self, task_num):
        while True:
            dirpath = self.unsearched.get()
            dirs = self.__explore_path(task_num, dirpath)
            for newdir in dirs:
                self.unsearched.put(newdir)
            self.unsearched.task_done()


parser = argparse.ArgumentParser()
parser.add_argument("-p", "--path", help="file/dir path", action="store", dest="path", default=".", required=True)
args = parser.parse_args()

crawler = TreeCrawler(args.path)
crawler.run_crawler()

print 'Done'
