# from os import listdir
# from os.path import isfile
import os
import json

class TBlock:
	def __init__(self, blockHash, parentHash):
		self.Hash = blockHash
		self.Parent = parentHash
		self.Childs = []

	def SetParent(self, parent):
		self.Parent = parent

	def AddChild(self, childHash):
		for i in xrange(len(self.Childs)):
			if self.Childs[i][0] == childHash:
				self.Childs[i] = (self.Childs[i][0], self.Childs[i][1] + 1)
				return
		self.Childs.append((childHash, 1))

	def SortChilds(self):
		self.Childs.sort(key = lambda x: -x[1])

	def __str__(self):
		return '\n' + self.Hash + '\n' + self.Parent + '\n' + str(self.Childs) + '\n'

	def ToDict(self):
		return {'Hash': self.Hash, 'Parent': self.Parent, 'Childs': self.Childs}


def buildTree():
	mypath = './data'
	onlyfiles = [f for f in os.listdir(mypath) if (os.path.isfile(os.path.join(mypath, f)) and f.startswith("data_"))]
	blocksTree = dict()

	for input_file in onlyfiles:
		with open(os.path.join(mypath, input_file), 'r') as f:
			for line in f:
				prevBlockHash, nextBlockHash, timeEdge = line.split()
				if prevBlockHash not in blocksTree:
					blocksTree[prevBlockHash] = TBlock(prevBlockHash, str(-1))
				if nextBlockHash not in blocksTree:
					blocksTree[nextBlockHash] = TBlock(nextBlockHash, str(-1))

				blocksTree[nextBlockHash].SetParent(prevBlockHash)
				blocksTree[prevBlockHash].AddChild(nextBlockHash)

	result = []
	for blockHash, block in blocksTree.iteritems():
		block.SortChilds()
		result.append(block.ToDict())

	with open('result.json', 'w') as g:
		json.dump(result, g, indent=4, sort_keys=True)

if __name__ == "__main__":
	buildTree()

