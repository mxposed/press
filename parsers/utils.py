

def inspect(node, name=None, num='N', indent=0):
    val = None
    left = True
    if hasattr(node, 'value'):
        val = node.value
        children = 0
    elif hasattr(node, 'subject'):
        val = 'call {}: {}'.format(node.subject, node.args)
        children = 0
    elif hasattr(node, 'text'):
        val = node.text
        children = len(node.elements)
        left = False
    else:
        val = node.__class__.__name__
        children = 0

    print('{}{} | {} | {} | {} child nodes'.format(
        ' ' * indent,
        val,
        name or '    ',
        num,
        children
    ))
    if left:
        return
    names = list(filter(lambda x: not x.startswith('__'), dir(node)))
    names.remove('text')
    names.remove('offset')
    names.remove('elements')
    for i, child in enumerate(node.elements):
        name = None
        for n in names:
            if getattr(node, n) == child:
                name = n
        inspect(child, name, i, indent + 2)


def traverse(node, child_indices):
    for i in child_indices:
        node = node.elements[i]
    return node
