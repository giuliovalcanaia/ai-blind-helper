from google import genai
from google.genai import types
from config import Config
from datetime import datetime
import os
import json


today = datetime.now().strftime("%Y-%m-%d")
day_of_the_week = datetime.now().strftime("%A")
time = datetime.now().strftime("%H:%M")




def persist_appointment(date, time, topic):
    filename = "appointments.json"
    new_event = {"date": date, "time": time, "topic": topic}
    
    # Carrega dados existentes ou cria nova lista
    data = []
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

    data.append(new_event)
    
    # Salva no arquivo
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    return {"status": "sucess", "message": f"Appointment {topic} saved to {date} {time}"}


available_functions = {
    "persist_appointment": persist_appointment
}

tool_definition = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="persist_appointment", # Use o mesmo nome da função real
            description="Schedules a meeting at a given time and date.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "date": types.Schema(type="STRING", description="Date (YYYY-MM-DD)"),
                    "time": types.Schema(type="STRING", description="Time (HH:MM)"),
                    "topic": types.Schema(type="STRING", description="Topic of the meeting"),
                },
                required=["date", "time", "topic"]
            )
        )
    ]
)


# Define the function declaration for the model
schedule_meeting_function = {
    "name": "schedule_meeting",
    "description": "Schedules a meeting at a given time and date.",
    "parameters": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "Date of the meeting (e.g., '2024-07-29')",
            },
            "time": {
                "type": "string",
                "description": "Time of the meeting (e.g., '15:00')",
            },
            "topic": {
                "type": "string",
                "description": "The subject or topic of the meeting.",
            },
        },
        "required": ["date", "time", "topic"],
    },
}


# Configure the client and tools
client = genai.Client(api_key=Config.API_KEY)
# tools = types.Tool(function_declarations=[schedule_meeting_function])
config = types.GenerateContentConfig(tools=[tool_definition], system_instruction = f"Today is {day_of_the_week}, date: {today}, time: {time}. When scheduling appointments, convert relative terms like 'tomorrow' or days of the week into the correct date in YYYY-MM-DD format.")

# Send request with function declarations
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Schedule a math class for tomorrow at 10:00",
    config=config,
)

for part in response.candidates[0].content.parts:
    if part.function_call:
        fn_name = part.function_call.name
        fn_args = part.function_call.args
        
        print(f"Chamando função: {fn_name} com {fn_args}")
        
        # EXECUÇÃO REAL: Aqui é onde o arquivo .json será criado
        if fn_name in available_functions:
            function_to_call = available_functions[fn_name]
            # O SDK retorna os argumentos como um dicionário, podemos desempacotá-los
            result = function_to_call(**fn_args)
            print(f"Resultado da função: {result}")
            
            # (Opcional) Enviar o resultado de volta para o modelo para ele confirmar ao usuário
            # response_confirmation = client.models.generate_content(...)
        else:
            print(f"Erro: Função {fn_name} não encontrada no mapeamento.")
