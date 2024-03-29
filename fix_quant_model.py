

import onnx
import onnx_graphsurgeon as gs


import numpy as np


if __name__ == "__main__":
    graph = gs.import_onnx(onnx.load("encoder_quant.onnx"))

    tmap = graph.tensors()
    # You can figure out the input and output tensors using Netron. In our case:
    # Inputs: [inp, MIN_VAL, MAX_VAL]
    # Outputs: [max_out]
    
    for node in graph.nodes:
        if node.op =="Conv":
            bias_node = node.inputs[2].inputs[0]
            bias_val = bias_node.inputs[0].values * bias_node.inputs[1].values
            node.inputs[2] = gs.Constant(bias_node.name, bias_val)
    
    for node in graph.nodes:
        if node.op =="DequantizeLinear" and \
                isinstance(node.inputs[0], gs.ir.tensor.Constant):
            if node.name in ["1006_DequantizeLinear", "encoder.encoders.1.norm_ff.weight_DequantizeLinear"]:
                print(node)
            if len(node.inputs[0].values.shape)==0:
                # print(node.inputs[0].values.shape)
                node.inputs[0].values.shape = (1,) # len(node.inputs[0].values.tolist())
                # print(node.inputs[0].values.shape)
            const_w = gs.Constant(node.inputs[0].name, node.inputs[0].values.astype(np.float32))
            attrs_dict = {}
            Cast_output = gs.Variable(name=node.inputs[0].name+"_Cast_output", 
                dtype=None, shape=None)
            attrs_dict['to'] = 3    #   int8
            newNode = gs.Node(name=node.inputs[0].name+"_Cast", op="Cast", inputs=[const_w],
                      outputs=[Cast_output], attrs=attrs_dict)
            graph.nodes.append(newNode)  # 记得把新节点加入计算图中
            node.inputs[0] = Cast_output
    # Remove the now-dangling subgraph.
    graph.cleanup().toposort()

    # That's it!
    onnx.save(gs.export_onnx(graph), "encoder_quant_fixed.onnx")





