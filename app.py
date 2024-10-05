from flask import Flask, request, render_template, redirect, url_for, session
import openai
import os
from dotenv import load_dotenv

# Cargar las variables de entorno
load_dotenv()

# Inicializar la aplicación Flask
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Necesario para usar 'session'

# Obtener la clave desde la variable de entorno
api_key = os.getenv("OPENAI_API_KEY")

# Verificar si la clave de API se ha cargado correctamente
if not api_key:
    raise ValueError("No se encontró la clave de OpenAI. Asegúrate de que está definida en el archivo .env.")

# Configurar la clave de OpenAI
openai.api_key = api_key

# Ruta principal para mostrar el formulario de entrada
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para procesar el tema ingresado y generar texto original
@app.route('/process', methods=['POST'])
def process():
    # Obtener el tema ingresado por el usuario
    topic = request.form.get('topic')
    if not topic:
        return "No se ha ingresado ningún tema."

    # Guardar el tema en la sesión
    session['topic'] = topic

    # Generar el texto original sobre el tema
    prompt_text = [
        {"role": "system", "content": "Eres un experto en educación que debe generar un texto educativo serio sobre el tema que el usuario elija."},
        {"role": "user", "content": f"Escribe un texto educativo serio sobre el tema: {topic}"}
    ]
    
    # Llamada a la API para generar el texto educativo original
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=prompt_text,
            temperature=0.7,
            max_tokens=1500
        )
        original_text = response['choices'][0]['message']['content']
        
        # Guardar el texto original en la sesión
        session['original_text'] = original_text
        
        # Redirigir a la página que muestra el texto original
        return redirect(url_for('show_original_text'))

    except openai.error.OpenAIError as e:
        return f"Error en la API de OpenAI: {e}"
    except Exception as e:
        return f"Ocurrió un error: {e}"

# Mostrar el texto original
@app.route('/show_original_text')
def show_original_text():
    original_text = session.get('original_text')
    if not original_text:
        return redirect(url_for('index'))
    return render_template('original_text.html', original_text=original_text)

# Ruta para mostrar el cuestionario del texto original
@app.route('/original_test', methods=['GET', 'POST'])
def original_quiz():
    original_text = session.get('original_text')
    if not original_text:
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Aquí puedes procesar las respuestas del cuestionario del texto original
        # Luego, redirigir a la versión humorística
        return redirect(url_for('show_humor_text'))
    
    # Generar preguntas sobre el tema en la versión seria
    prompt_questions = [
        {"role": "system", "content": "Genera cinco preguntas de opción múltiple sobre el siguiente texto: "},
        {"role": "user", "content": original_text}
    ]
    
    response_questions = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=prompt_questions,
        temperature=0.7,
        max_tokens=500
    )
    
    questions = response_questions['choices'][0]['message']['content']
    
    return render_template('original_test.html', questions=questions)

# Mostrar el texto humorístico
@app.route('/show_humor_text')
def show_humor_text():
    original_text = session.get('original_text')
    if not original_text:
        return redirect(url_for('index'))

    # Generar la versión humorística del mismo texto
    prompt_humor = [
        {"role": "system", "content": "Transforma el siguiente texto en un estilo humorístico adecuado para adolescentes: "},
        {"role": "user", "content": original_text}
    ]
    
    response_humor = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=prompt_humor,
        temperature=0.7,
        max_tokens=1500
    )
    
    humor_text = response_humor['choices'][0]['message']['content']
    
    # Guardar el texto humorístico en la sesión
    session['humor_text'] = humor_text

    return render_template('humor_text.html', humor_text=humor_text)

# Ruta para mostrar el cuestionario del texto humorístico
@app.route('/humor_test', methods=['GET', 'POST'])
def humor_test():
    humor_text = session.get('humor_text')
    if not humor_text:
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Aquí puedes procesar las respuestas del cuestionario humorístico
        # Luego, redirigir a la encuesta final
        return redirect(url_for('survey'))
    
    # Generar preguntas sobre el texto humorístico
    prompt_questions = [
        {"role": "system", "content": "Genera cinco preguntas de opción múltiple sobre el siguiente texto: "},
        {"role": "user", "content": humor_text}
    ]
    
    response_questions = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=prompt_questions,
        temperature=0.7,
        max_tokens=500
    )
    
    questions = response_questions['choices'][0]['message']['content']
    
    return render_template('humor_test.html', questions=questions)

# Ruta para mostrar la encuesta final de retroalimentación
@app.route('/survey', methods=['GET', 'POST'])
def survey():
    if request.method == 'POST':
        # Procesar las respuestas de la encuesta
        original_rating = request.form.get('original_rating')
        humor_rating = request.form.get('humor_rating')
        # Aquí puedes guardar los resultados o procesarlos como necesites
        return "¡Gracias por tu participación!"

    return render_template('survey.html')

# Ejecutar la aplicación Flask
if __name__ == '__main__':
    app.run(debug=True)
