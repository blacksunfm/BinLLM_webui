#!/usr/bin/env python
# -*- coding: utf-8 -*-
# combined_export.py - Export both decompiled C code and disassembly (Jython 2.7 compatible)

import os
import json
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
import datetime

def get_decompiled_c(function):
    """Get decompiled C code for a function"""
    try:
        decompiler = DecompInterface()
        decompiler.openProgram(currentProgram)
        decompile_results = decompiler.decompileFunction(function, 30, ConsoleTaskMonitor())
        return decompile_results.getDecompiledFunction().getC()
    except Exception as e:
        print("Decompilation failed for %s: %s" % (function.getName(), str(e)))
        return "/* Decompilation failed */"

def get_disassembly(function, program):
    """Get disassembly for a function"""
    disassembly = []
    try:
        listing = program.getListing()
        code_units = listing.getCodeUnits(function.getBody(), True)
        
        for code_unit in code_units:
            disassembly.append({
                "address": "0x{}".format(code_unit.getAddress()),
                "code": str(code_unit.toString())
            })
    except Exception as e:
        print("Disassembly failed for %s: %s" % (function.getName(), str(e)))
        disassembly.append({"error": "Failed to get disassembly"})
    
    return disassembly

def export_function_data():
    try:
        # 优先使用环境变量OUTPUT_FILE
        output_file = os.environ.get('OUTPUT_FILE')
        if not output_file:
            # 自动生成：与分析文件同目录，文件名为 <原文件名>_ghidra_<日期>.json
            program = currentProgram
            if program is None:
                raise Exception("Failed to get current program")
            bin_path = program.getExecutablePath()
            bin_name = os.path.basename(bin_path)
            date_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(os.path.dirname(bin_path), '{}_ghidra_{}.json'.format(bin_name, date_str))
        print("Output will be saved to: " + output_file)
        
        program = currentProgram
        if program is None:
            raise Exception("Failed to get current program")
            
        result = {
            "program_info": {
                "name": str(program.getName()),
                "executable_format": str(program.getExecutableFormat()),
                "language_id": str(program.getLanguageID()),
                "compiler_spec_id": str(program.getCompilerSpec().getCompilerSpecID())
            },
            "functions": []
        }
        
        function_manager = program.getFunctionManager()
        functions = list(function_manager.getFunctions(True))
        
        print("Processing %d functions..." % len(functions))
        
        for function in functions:
            func_name = str(function.getName())
            print("Processing function: " + func_name)
            
            func_data = {
                "name": func_name,
                "entry_point": "0x%s" % function.getEntryPoint(),
                "signature": str(function.getSignature(True)),
                "c_code": get_decompiled_c(function),
                "disassembly": get_disassembly(function, program)
            }
            
            result["functions"].append(func_data)
        
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
            
        print("Successfully exported data to " + output_file)
        
    except Exception as e:
        print("Export failed: " + str(e))
        raise

if 'currentProgram' in globals():
    export_function_data()
else:
    print("Error: Must be run within Ghidra")

# analyzeHeadless F:\Ghidra test -import C:\Users\blacksun\Downloads\example.exe -postScript F:\Ghidra\get_function_json.py -overwrite