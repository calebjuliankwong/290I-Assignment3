from fastapi import FastAPI, File, UploadFile
from typing_extensions import Annotated
import uvicorn
from utils import *
from dijkstra import dijkstra

# create FastAPI app
app = FastAPI()

# global variable for active graph
active_graph = None

@app.get("/")
async def root():
    return {"message": "Welcome to the Shortest Path Solver!"}


@app.post("/upload_graph_json/")
async def create_upload_file(file: UploadFile):
    """
    Uploads a JSON graph file and stores it in memory.
    """
    global active_graph

    # Check file extension
    if not file.filename.endswith(".json"):
        return {"Upload Error": "Invalid file type"}

    try:
        # Read and parse JSON
        contents = await file.read()
        graph = json.loads(contents.decode("utf-8"))

        # Store graph in memory
        active_graph = graph
        return {"Upload Success": file.filename}

    except json.JSONDecodeError:
        return {"Upload Error": "Invalid JSON format"}



@app.get("/solve_shortest_path/start_node_id={start_node_id}&end_node_id={end_node_id}")
async def get_shortest_path(start_node_id: str, end_node_id: str):
    """
    Solves the shortest path using the uploaded graph.
    """
    global active_graph

    if not active_graph:
        return {"Solver Error": "No active graph, please upload a graph first."}

    try:
        from graph import Graph
        from node import Node
        from dijkstra import dijkstra

        g = Graph()

        # Create Node objects and map IDs to Nodes
        node_map = {}
        for edge in active_graph:
            for node_id in [edge["source"], edge["target"]]:
                node_id = str(node_id)
                if node_id not in node_map:
                    node_obj = Node(node_id)
                    node_map[node_id] = node_obj
                    g.add_node(node_obj)

        # Add edges using Node objects
        for edge in active_graph:
            src = node_map[str(edge["source"])]
            tgt = node_map[str(edge["target"])]
            weight = edge["weight"]
            bidirectional = edge.get("bidirectional", False)
            g.add_edge(src, tgt, weight, bidirectional)

        # Identify start and end nodes
        start_node = node_map.get(str(start_node_id))
        end_node = node_map.get(str(end_node_id))

        if start_node is None or end_node is None:
            return {"Solver Error": "Invalid start or end node ID."}

        # Run Dijkstra (it modifies the nodes in the graph)
        dijkstra(g, start_node)

        # Reconstruct path from end_node.prev
        path = []
        current = end_node
        while current is not None:
            path.append(current.id)
            current = current.prev
        path.reverse()

        if not path or path[0] != str(start_node_id):
            return {"Solver Error": f"No path exists between {start_node_id} and {end_node_id}."}

        return {
            "path": path,
            "distance": end_node.dist
        }

    except Exception as e:
        return {"Solver Error": str(e)}
   
   





if __name__ == "__main__":
    print("Server is running at http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
    