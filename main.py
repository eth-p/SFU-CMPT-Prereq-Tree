import dagger
import json
from graphviz import Source

COURSE_JSON_DIR = "./courses.json"
RESULT_DIR = "./result/tree.dot"


def dot_file_fixes():
  dot_file = open(RESULT_DIR, "r")
  lines = dot_file.readlines()
  lines.insert(2, "edge [dir = back];\n")
  dot_file = open(RESULT_DIR, "w")
  dot_file.writelines(lines)
  dot_file.close()


def export():
  dot_graph = Source.from_file(RESULT_DIR, format="svg", engine="dot")
  dot_graph.render()


def main():
  dag = dagger.dagger()
  course_file = open(COURSE_JSON_DIR, "r")
  data = json.load(course_file)
  course_file.close()

  # Add nodes and others they depend on
  for course in data["COURSES"]:
    dag.add(course["CODE"], course["PREREQ"])

  # Evaluate the graph
  dag.run()

  # Export for visualizing
  dag.dot(RESULT_DIR)
  dot_file_fixes()
  export()

if __name__ == "__main__":
  main()
