# from os import listdir
# from os.path import isfile
import os
import json

class TBlock:
	def __init__(self, blockHash, parentHash):
		self.Hash = blockHash
		self.Parent = parentHash
		self.Childs = []
		self.Mark = -1
		self.Depth = 0

	def SetParent(self, parent):
		self.Parent = parent

	def AddChild(self, childHash):
		for i in xrange(len(self.Childs)):
			if self.Childs[i][0] == childHash:
				return
		self.Childs.append((childHash, 0))

	def SortChilds(self):
		self.Childs.sort(key = lambda x: -x[1])

	def __str__(self):
		return '\n' + self.Hash + '\n' + self.Parent + '\n' + str(self.Childs) + '\n'

	def ToDict(self):
		return {"Hash": self.Hash, 'Parent': self.Parent, 'Childs': self.Childs, 'BranchMark': self.Mark, "Depth": self.Depth}


def FindRoot(blocksTree):
	for key, value in blocksTree.iteritems():
		if value.Parent == "-1":
			return key

class BranchNumber:
	def __init__(self):
		self.Number = 0
	def GetNumber(self):
		return self.Number
	def AddNumber(self):
		self.Number += 1

def FindBranches(rootHash, blocksTree, branchNumber):
	mark = branchNumber.GetNumber()
	blocksTree[rootHash].Mark = mark
	if len(blocksTree[rootHash].Childs) > 0:
		FindBranches(blocksTree[rootHash].Childs[0][0], blocksTree, branchNumber)
		for i in xrange(1, len(blocksTree[rootHash].Childs)):
			branchNumber.AddNumber()
			FindBranches(blocksTree[rootHash].Childs[i][0], blocksTree, branchNumber)


def GetFinalOrder(rootHash, blocksTree, finalOrder):
	q = list()
	was = set()
	q.append(rootHash)
	while len(q) > 0:
		r = q[0]
		finalOrder.append(blocksTree[r])
		del q[0]
		was.add(r)
		if len(blocksTree[r].Childs) > 0:
			for i in xrange(0, len(blocksTree[r].Childs)):
				if blocksTree[r].Childs[i][0] not in was:
					q.append(blocksTree[r].Childs[i][0])
					# GetFinalOrder(blocksTree[r].Childs[i][0], blocksTree, finalOrder)

def UpdateDepth(rootHash, blocksTree):
	for i in xrange(len(blocksTree[rootHash].Childs)):
		childHash = blocksTree[rootHash].Childs[i][0]
		UpdateDepth(childHash, blocksTree)
		blocksTree[rootHash].Childs[i] = (blocksTree[rootHash].Childs[i][0], blocksTree[childHash].Depth)
		blocksTree[rootHash].Depth = max(blocksTree[rootHash].Depth, blocksTree[childHash].Depth + 1)



def buildTree():
	mypath = '../fork_data'
	onlyfiles = [f for f in os.listdir(mypath) if (os.path.isfile(os.path.join(mypath, f)) and f.startswith("data"))]
	blocksTree = dict()
	print onlyfiles
	for input_file in onlyfiles:
		with open(os.path.join(mypath, input_file), 'r') as f:
			for line in f:
				prevBlockHash, nextBlockHash, timeEdge = line.split()
				if prevBlockHash not in blocksTree:
					blocksTree[prevBlockHash] = TBlock(prevBlockHash, str(-1))
				if nextBlockHash not in blocksTree:
					blocksTree[nextBlockHash] = TBlock(nextBlockHash, str(-1))
				else:
					if blocksTree[nextBlockHash].Parent != prevBlockHash:
						print 'ASSERT'
						continue

				blocksTree[nextBlockHash].SetParent(prevBlockHash)
				blocksTree[prevBlockHash].AddChild(nextBlockHash)

	result = []
	rootHash = FindRoot(blocksTree)

	UpdateDepth(rootHash, blocksTree)

	for blockHash, block in blocksTree.iteritems():
		block.SortChilds()

	branchNumber = BranchNumber()
	FindBranches(rootHash, blocksTree, branchNumber)


	finalOrder = []
	GetFinalOrder(rootHash, blocksTree, finalOrder)

	for block in finalOrder:
		result.append(block.ToDict())
	#for blockHash, block in blocksTree.iteritems():
	#	result.append(block.ToDict())



	with open('result.json', 'w') as g:
		print >>g, 'var graphJson = {0};'.format(json.dumps(result, g, indent=4, sort_keys=True))

if __name__ == "__main__":
	buildTree()

