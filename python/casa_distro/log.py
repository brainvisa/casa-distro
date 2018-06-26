# coding: utf-8 

def getLogFile(verbose, openmode='w+'):
    import ast, types, sys
    
    if isinstance(verbose, types.StringTypes):
        try:
            # Try to interpret string as boolean or integer values
            verbose = ast.literal_eval(verbose.title())
            
        except:
            # Try to open file from given string
            try:
                verbose = open(verbose, openmode)
            except:
                pass
    
    if isinstance(verbose, (types.IntType, types.BooleanType)):
        return sys.stdout if verbose else None
    
    if isinstance(verbose, (types.FileType, types.NoneType)):
        return verbose
    
    return None
