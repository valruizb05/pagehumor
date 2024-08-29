from flask import Flask, request, render_template, send_file
import openai
import os
import PyPDF2
from dotenv import load_dotenv

load_dotenv()

# Obtener la clave desde la variable de entorno
api_key = os.getenv("OPENAI_API_KEY")

# Usar la clave API en tu código
print(api_key)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    if 'pdf' not in request.files:
        return "No se ha subido ningún archivo PDF."
    
    pdf_file = request.files['pdf']

    # Leer el contenido del archivo PDF
    try:
        pdf_reader = PyPDF2.PdfFileReader(pdf_file)
        text_content = ""
        for page_num in range(pdf_reader.getNumPages()):
            text_content += pdf_reader.getPage(page_num).extract_text()
    except Exception as e:
        return f"Ocurrió un error al leer el archivo PDF: {e}"

    # Generar el prompt para la API
    prompt = [
        {"role": "system", "content": "Transforma este texto en un estilo humorístico adecuado para adolescentes, considerando los elementos de incongruencia, exageración y personificación."},
        {"role": "user", "content": text_content}
    ]

    # Llamar a la API de OpenAI
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=prompt,
            temperature=0.1,
            max_tokens=3000
        )
        
        transformed_text = response['choices'][0]['message']['content']

        # Guardar el texto transformado en un archivo de texto
        output_file_path = 'transformed_text.txt'
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.write(transformed_text)

        return send_file(output_file_path, as_attachment=True)

    except openai.error.OpenAIError as e:
        return f"Error en la API de OpenAI: {e}"
    except Exception as e:
        return f"Ocurrió un error al procesar el texto: {e}"

if __name__ == '__main__':
    app.run(debug=True)
