import llama_index
import pkgutil

# Check if 'postprocessors' exists
if hasattr(llama_index, 'postprocessors'):
    print("postprocessors module exists.")
    # List submodules within 'postprocessors'
    for importer, modname, ispkg in pkgutil.iter_modules(llama_index.postprocessors.__path__):
        print(modname)
else:
    print("postprocessors module does not exist.")