from flask import Flask, request, render_template, redirect, url_for, session
import openai
import os
from dotenv import load_dotenv
import pandas as pd

# Cargar las variables de entorno
load_dotenv()

# Inicializar la aplicación Flask y configurar la carpeta de archivos estáticos
app = Flask(__name__, static_folder='style')
app.secret_key = 'supersecretkey'

# Obtener la clave desde la variable de entorno
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("No se encontró la clave de OpenAI.")

# Configurar la clave de OpenAI
openai.api_key = api_key

@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://www.gstatic.com; "
        "script-src 'self' 'unsafe-inline';"
    )
    return response

# Ruta principal
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        button_value = request.form.get('button')  # Identificar qué botón fue presionado

        # Guardar la opción seleccionada en la sesión
        session['option'] = button_value

        # Redirigir según la opción seleccionada
        if button_value == '1':  # Proceso completo
            return redirect(url_for('personal_data'))
        elif button_value == '2':  # Solo texto humorístico
            return redirect(url_for('ask_topic'))
    
    return render_template('index.html')


# Solicitar datos personales (solo para Opción 1)
@app.route('/personal_data', methods=['GET', 'POST'])
def personal_data():
    if request.method == 'POST':
        # Guardar los datos personales en la sesión
        session['name'] = request.form.get('name')
        session['surname'] = request.form.get('surname')
        session['age'] = request.form.get('age')
        session['education'] = request.form.get('education')
        
        # Redirigir a la página donde se selecciona el tema
        return redirect(url_for('ask_topic'))
    
    return render_template('personal_data.html')


# Solicitar el tema
@app.route('/ask_topic', methods=['GET', 'POST'])
def ask_topic():
    if request.method == 'POST':
        # Obtener el tema ingresado
        topic = request.form.get('topic')
        
        if topic:
            session['topic'] = topic

            # Redirigir según la opción seleccionada en el inicio
            if session.get('option') == '1':  # Opción 1: Proceso completo
                return redirect(url_for('show_original_text'))
            elif session.get('option') == '2':  # Opción 2: Solo texto humorístico
                return redirect(url_for('show_humor_text'))
        else:
            return "No se ingresó ningún tema", 400  # Devolver un error si no se ingresa tema
    
    return render_template('ask_topic.html')


# Mostrar el texto original (solo para Opción 1)
@app.route('/show_original_text')
def show_original_text():
    topic = session.get('topic')
    
    # Generar el texto original basado en el tema
    prompt_text = [
        {"role": "system", "content": "Genera un texto educativo serio sobre el siguiente tema."},
        {"role": "user", "content": f"Escribe un texto educativo serio sobre: {topic}"}
    ]
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=prompt_text, temperature=0.7, max_tokens=1500)
    session['original_text'] = response['choices'][0]['message']['content']
    
    return render_template('original_text.html', original_text=session['original_text'])


@app.route('/original_test', methods=['GET', 'POST'])
def original_test():
    if request.method == 'POST':
        # Guardar la calificación del quiz
        session['original_score'] = request.form.get('score')
        return redirect(url_for('show_humor_text'))
    
    original_text = session.get('original_text')
    prompt_questions = [
        {"role": "system", "content": "Genera cinco preguntas de opción múltiple sobre el siguiente texto."},
        {"role": "user", "content": original_text}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=prompt_questions,
        max_tokens=500
    )
    
    # Procesar el contenido recibido en varias preguntas con opciones
    raw_questions = response['choices'][0]['message']['content']
    questions = raw_questions.split("\n\n")  # Divide las preguntas por doble salto de línea

    formatted_questions = []
    for question in questions:
        # Extraer la pregunta y las opciones (asumiendo que las opciones empiezan con letras a), b), c)...)
        lines = question.split("\n")
        pregunta = lines[0]
        opciones = lines[1:]  # Extrae las opciones
        
        formatted_questions.append({
            'pregunta': pregunta,
            'opciones': opciones
        })

    return render_template('original_test.html', questions=formatted_questions)


# Mostrar el texto humorístico
@app.route('/show_humor_text')
def show_humor_text():
    original_text = session.get('original_text')
    
    # Generar la versión humorística del texto
    prompt_humor = [
        {"role": "system", "content": "Transforma el siguiente texto en un estilo humorístico adecuado para adolescentes."},
        {"role": "user", "content": original_text}
    ]
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=prompt_humor, max_tokens=1500)
    session['humor_text'] = response['choices'][0]['message']['content']
    
    return render_template('humor_text.html', humor_text=session['humor_text'])


@app.route('/humor_test', methods=['GET', 'POST'])
def humor_test():
    if request.method == 'POST':
        # Guardar la calificación del quiz de humor
        session['humor_score'] = request.form.get('score')
        return redirect(url_for('survey'))
    
    humor_text = session.get('humor_text')
    prompt_questions = [
        {"role": "system", "content": "Genera cinco preguntas de opción múltiple sobre el siguiente texto humorístico."},
        {"role": "user", "content": humor_text}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=prompt_questions,
        max_tokens=500
    )
    
    # Convertimos las preguntas en una lista para enviarlas a la plantilla
    questions = response['choices'][0]['message']['content'].split("\n")
    
    return render_template('humor_test.html', questions=questions)


@app.route('/survey', methods=['GET', 'POST'])
def survey():
    if request.method == 'POST':
        original_percentage = request.form.get('original_percentage')
        humor_percentage = request.form.get('humor_percentage')
        
        # Determinar el archivo donde guardar los resultados según la opción
        if session.get('option') == '1':  # Opción 1: Proceso completo
            # Guardar también los datos personales
            data = {
                'Name': [session['name']],
                'Surname': [session['surname']],
                'Age': [session['age']],
                'Education': [session['education']],
                'Original Score': [session['original_score']],
                'Humor Score': [session['humor_score']],
                'Original Percentage': [original_percentage],
                'Humor Percentage': [humor_percentage]
            }
            file_path = 'quiz_results.xlsx'
        elif session.get('option') == '2':  # Opción 2: Solo texto humorístico
            # Guardar solo las calificaciones y porcentajes sin datos personales
            data = {
                'Humor Score': [session['humor_score']],
                'Humor Percentage': [humor_percentage]
            }
            file_path = 'humor_only_results.xlsx'

        df = pd.DataFrame(data)

        # Crear la carpeta 'data' si no existe
        if not os.path.exists('data'):
            os.makedirs('data')

        # Ruta completa para el archivo
        full_path = os.path.join('data', file_path)

        # Si el archivo existe, cargarlo y agregar los nuevos datos
        if os.path.exists(full_path):
            existing_df = pd.read_excel(full_path)
            df = pd.concat([existing_df, df], ignore_index=True)

        # Guardar los datos en el archivo adecuado
        df.to_excel(full_path, index=False)
        
        return "¡Gracias por tu participación!"
    
    return render_template('survey.html')

# Ejecutar la aplicación Flask
if __name__ == '__main__':
    app.run(debug=True)
