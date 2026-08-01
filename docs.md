

╭─ai-bootcamp-skeleton-main on 🌊 main 
╰─❯ python -m evaluation.evaluator
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Loading weights: 100%|███████████████████████████████████████████████████████████████████████████████████████████| 103/103 [00:00<00:00, 2432.71it/s]
<class 'langchain_core.messages.human.HumanMessage'>
content='How many annual leave days do I have remaining?' additional_kwargs={} response_metadata={} id='b9fe47ab-524e-47fd-9049-ff658953dca9'
--------------------------------------------------------------------------------
<class 'langchain_core.messages.ai.AIMessage'>
content='' additional_kwargs={} response_metadata={} id='e137b200-d083-4778-8801-570d5971e2de' tool_calls=[{'name': 'check_balance', 'args': {'employee_id': 'E001', 'leave_type': 'annual'}, 'id': 'call_kzEBqDh5TCqiB4OhiwsG3TpL', 'type': 'tool_call'}] invalid_tool_calls=[]
--------------------------------------------------------------------------------
<class 'langchain_core.messages.tool.ToolMessage'>
content='[{"employee_id": "E001", "leave_type": "annual", "remaining_days": 11}]' id='a8fab84e-4eac-4844-aedb-4e6f275cd7e6' tool_call_id='call_kzEBqDh5TCqiB4OhiwsG3TpL'
--------------------------------------------------------------------------------
<class 'langchain_core.messages.ai.AIMessage'>
content='You have 11 annual leave days remaining.' additional_kwargs={} response_metadata={} id='f2db9cc1-151b-4203-90c0-e13417740359' tool_calls=[] invalid_tool_calls=[]
--------------------------------------------------------------------------------

╭─ai-bootcamp-skeleton-main on 🌊 main 
╰─❯ 