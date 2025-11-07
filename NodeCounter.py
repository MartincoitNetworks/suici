import NotionTools as nt


def printAllEdges():

    print("Reading list of Edges from Notion...", end="")
    edges = nt.getAllAutoConfigEdges()

    for edge in edges:
        print(edge)

    return


def CountAllNodesAllEdges():
    return 0

if __name__ == "__main__":
    print("Welcome")
    printAllEdges()

