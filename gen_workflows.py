def spawn_workflow(num):
    w = WorkflowJobTemplate()
    w.name = "w1"
    w.save()
    prev_node = None
    for _ in range(num):
        node = WorkflowJobTemplateNode()
        # 10 was a job template I had created previously
        node.unified_job_template_id = 10
        node.workflow_job_template_id = w.id
        node.save()
        if prev_node:
            prev_node.success_nodes.add(node)
            prev_node.save()
        else:
            w.workflow_job_template_nodes.add(node)
            w.save()
        prev_node = node


def spawn_fan(pnode, wid, fan, depth):
    if depth == 0:
        return
    for _ in range(fan):
        node = WorkflowJobTemplateNode()
        node.unified_job_template_id = 10
        node.workflow_job_template_id = wid
        node.save()
        pnode.success_nodes.add(node)
        spawn_fan(node, wid, fan, depth - 1)
    pnode.save()


def spawn_workflow_fan(depth, fan):
    w = WorkflowJobTemplate()
    w.name = "w2"
    w.save()
    node = WorkflowJobTemplateNode()
    node.unified_job_template_id = 10
    node.workflow_job_template_id = w.id
    node.save()
    w.workflow_job_template_nodes.add(node)
    w.save()
    spawn_fan(node, w.id, fan, depth)



spawn_workflow_fan(3,3)
