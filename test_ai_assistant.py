import requests
import json

# URL do seu endpoint do assistente de IA
# Certifique-se de que seu servidor Django esteja rodando em http://127.0.0.1:8000/
API_URL = "http://127.0.0.1:8000/api/ai-assistant/"

def ask_ai_assistant(question):
    """
    Envia uma pergunta para o assistente de IA e retorna a resposta.
    """
    headers = {
        "Content-Type": "application/json",
    }
    payload = {
        "question": question,
    }

    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Levanta um erro para status HTTP ruins (4xx ou 5xx)

        data = response.json()
        if "answer" in data:
            return data["answer"]
        elif "error" in data:
            return f"Erro da API: {data['error']}"
        else:
            return f"Resposta inesperada da API: {data}"

    except requests.exceptions.ConnectionError:
        return "Erro de conexão: Certifique-se de que o servidor Django está rodando."
    except requests.exceptions.RequestException as e:
        return f"Erro na requisição: {e}"
    except json.JSONDecodeError:
        return f"Erro ao decodificar JSON da resposta: {response.text}"

if __name__ == "__main__":
    print("--- Teste do Assistente de IA BarberFlow ---")
    print("Digite 'sair' para encerrar.")

    while True:
        user_input = input("\nSua pergunta: ")
        if user_input.lower() == 'sair':
            break

        print("Consultando assistente de IA...")
        answer = ask_ai_assistant(user_input)
        print(f"Resposta do AI: {answer}")

    print("\nTeste encerrado.")