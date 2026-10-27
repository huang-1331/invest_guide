"""Execute all notebook cells in order using an actual in-process IPython shell.

The restricted runner disallows TCP and Unix sockets, so Jupyter kernel startup
is unavailable here. This executes Python cells without sockets; it is not a
Jupyter-kernel execution. The execution engine is recorded in notebook metadata.
"""
import os
from pathlib import Path
import nbformat
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
root=Path(__file__).resolve().parents[1]
path=root/'notebooks/research.ipynb'
nb=nbformat.read(path,as_version=4)
shell=InteractiveShell.instance()
os.chdir(root)
count=0
for cell in nb.cells:
    if cell.cell_type!='code':
        continue
    count+=1
    with capture_output() as captured:
        result=shell.run_cell(cell.source,store_history=True)
    outputs=[]
    if captured.stdout: outputs.append(nbformat.v4.new_output('stream',name='stdout',text=captured.stdout))
    if captured.stderr: outputs.append(nbformat.v4.new_output('stream',name='stderr',text=captured.stderr))
    for output in captured.outputs:
        outputs.append(nbformat.v4.new_output('display_data',data=output.data,metadata=output.metadata))
    cell.execution_count=count;cell.outputs=outputs
    if result.error_before_exec or result.error_in_exec:
        raise RuntimeError('Notebook cell execution failed: '+str(result.error_before_exec or result.error_in_exec))
nb.metadata['execution_engine']='in-process IPython; TCP/IPC kernel sockets unavailable in execution host'
nbformat.validate(nb)
nbformat.write(nb,path)
print('Executed',count,'code cells using in-process IPython; saved',path)
