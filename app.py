from flask import Flask, request, render_template, redirect, url_for, session
import openai
import os
from dotenv import load_dotenv
import pandas as pd
import secrets
import json
import re


# Cargar las variables de entorno
load_dotenv()

# Inicializar la aplicación Flask y configurar la carpeta de archivos estáticos
app = Flask(__name__, static_folder='static')
app.secret_key = secrets.token_hex(16)

# Configurar la clave de OpenAI desde las variables de entorno
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("No se encontró la clave de OpenAI. Asegúrate de que esté definida correctamente.")
openai.api_key = api_key

# Aplicar políticas de seguridad CSP
@app.after_request
def apply_csp(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "script-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.jsdelivr.net; "
        "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com https://cdn.jsdelivr.net"
    )
    return response

# Rutas de la aplicación
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/developers')
def developers():
    return render_template('developers.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/related')
def related():
    return render_template('related.html')

# Página de inicio con selección de opciones
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        button_value = request.form.get('button')
        if button_value == '1':  # Proceso completo
            session['option'] = button_value
            return redirect(url_for('personal_data'))
        elif button_value == '2':  # Solo texto humorístico
            session['option'] = button_value
            return redirect(url_for('ask_topic'))
    return render_template('index.html')



# Guardar datos personales y redirigir al cuestionario
@app.route('/personal_data', methods=['GET', 'POST'])
def personal_data():
    if request.method == 'POST':
        session['name'] = request.form.get('name')
        session['surname'] = request.form.get('surname')
        session['age'] = request.form.get('age')
        session['gender'] = request.form.get('gender')
        session['education'] = request.form.get('education')
        
        # Guardar datos personales en Excel
        save_data_to_excel(session['name'], session['surname'], session['age'], session['gender'], session['education'])
        
        return redirect(url_for('ask_topic'))
    return render_template('personal_data.html')



def save_data_to_excel(name, surname, age, gender, education, quiz_results=None):
    file_path = 'data/user_data.xlsx'
    
    user_data = {
        'Nombre': [name],
        'Apellidos': [surname],
        'Edad': [age],
        'Genero': [gender],
        'Educación': [education]
    }
    
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        user_row = df[(df['Nombre'] == name) & (df['Apellidos'] == surname)]
        
        if not user_row.empty:
            row_index = user_row.index[0]
            # Si hay resultados del quiz, los agrega como columnas adicionales en la misma fila
            if quiz_results:
                for question_id, result in quiz_results.items():
                    # Crea la columna si no existe y asigna el resultado (1 para correcta, 0 para incorrecta)
                    df.at[row_index, question_id] = result
        else:
            # Si el usuario no existe en el archivo, agrega una nueva fila con los datos personales
            df = pd.concat([df, pd.DataFrame(user_data)], ignore_index=True)
            # Agrega también los resultados del quiz en la nueva fila
            if quiz_results:
                for question_id, result in quiz_results.items():
                    df.at[df.index[-1], question_id] = result
    else:
        # Crea un nuevo DataFrame si el archivo no existe
        df = pd.DataFrame(user_data)
        # Agrega los resultados del quiz en la nueva fila
        if quiz_results:
            for question_id, result in quiz_results.items():
                df.at[0, question_id] = result
    
    # Guarda el DataFrame en el archivo Excel
    df.to_excel(file_path, index=False)


@app.route('/ask_topic', methods=['GET', 'POST'])
def ask_topic():
    if request.method == 'POST':
        # Obtener la categoría seleccionada
        category = request.form.get('category')
        session['category'] = category

        # Redirigir a la lista de textos de la categoría seleccionada
        return redirect(url_for('show_texts'))

    # Mostrar la página inicial para seleccionar la categoría
    return render_template('ask_topic.html')


@app.route('/show_texts', methods=['GET', 'POST'])
def show_texts():
    category = session.get('category')
    if not category:
        return redirect(url_for('ask_topic'))

    folder_path = os.path.join('data', 'Original', category)
    if not os.path.exists(folder_path):
        return f"No se encontraron textos en la categoría {category}"

    texts = [f for f in os.listdir(folder_path) if f.endswith('.txt')]

    if request.method == 'POST':
        # Obtener el valor de 'text' desde el formulario
        text = request.form.get('text')
        print("Texto recibido en /show_texts:", text)  # Imprime el valor recibido para depuración

        if text:
            session['text'] = text  # Guarda el nombre del archivo en la sesión correctamente
            print("Texto guardado en sesión:", session['text'])  # Imprime el valor guardado en la sesión
            return redirect(url_for('show_selected_text'))
        else:
            print("Error: No se seleccionó ningún texto.")
            return "Error: No se seleccionó ningún texto."

    return render_template('select_text_grid.html', texts=texts, category=category)


@app.route('/show_selected_text', methods=['GET', 'POST'])
def show_selected_text():
    category = session.get('category')
    text_file = session.get('text')  # Asegúrate de que 'text' esté en la sesión

    print("Categoría en sesión:", category)  # Depuración
    print("Archivo seleccionado en sesión:", text_file)  # Depuración

    if not text_file:
        return "Error: No se seleccionó ningún texto."

    folder_path = os.path.join('data', 'Original', category)
    file_path = os.path.join(folder_path, text_file)

    if not os.path.exists(file_path):
        return f"Error: No se encontró el archivo {file_path}"

    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    return render_template('show_text.html', content=content, category=category, text_file=text_file)


@app.route('/show_quiz')
def show_quiz():
    quiz = session.get('quiz')
    if not quiz:
        return "No se pudo generar el cuestionario."
    return render_template('quiz.html', quiz=quiz)


@app.route('/generate_quiz', methods=['POST'])
def generate_quiz_route():
    content = session.get('content')  # Asegúrate de que el contenido esté en la sesión o pásalo como parámetro
    quiz_json = generate_quiz(content)  # Llama a la función que generará el cuestionario con el LLM
    quiz = json.loads(quiz_json)  # Convierte el JSON en un diccionario de Python

    # Guarda el cuestionario y las respuestas correctas en la sesión
    session['quiz'] = quiz
    session['correct_answers'] = {f"question_{i+1}": q['respuesta_correcta'] for i, q in enumerate(quiz)}

    return redirect(url_for('generate_quiz_route'))


def generate_quiz(content):
    prompt = f"""
    Basado en el siguiente texto, crea un cuestionario de opción múltiple de 5 preguntas. 
    Cada pregunta debe tener 4 opciones y una de ellas debe ser la correcta. 
    Texto: "{content}"

    Devuelve únicamente el JSON sin ninguna explicación adicional en el siguiente formato:
    [
        {{
            "pregunta": "Pregunta aquí",
            "opciones": ["Opción A", "Opción B", "Opción C", "Opción D"],
            "respuesta_correcta": "Opción X"
        }},
        ...
    ]
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    
    response_text = response['choices'][0]['message']['content'].strip()
    
    # Validar si la respuesta es un JSON válido
    try:
        quiz = json.loads(response_text)  # Intenta cargar directamente como JSON
    except json.JSONDecodeError:
        raise ValueError("El modelo no devolvió un JSON válido")

    return response_text



@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    # Captura las respuestas del usuario
    user_answers = request.form.to_dict()  # Obtiene las respuestas del formulario como un diccionario
    correct_answers = session.get('correct_answers')  # Obtiene las respuestas correctas de la sesión

    # Inicializa contadores para las respuestas correctas e incorrectas
    score = 0
    total_questions = len(correct_answers)
    results = {}

    # Compara cada respuesta del usuario con la respuesta correcta
    for question_id, correct_answer in correct_answers.items():
        user_answer = user_answers.get(question_id)
        if user_answer == correct_answer:
            score += 1
            results[question_id] = 1  # Marca como correcta
        else:
            results[question_id] = 0  # Marca como incorrecta

    # Guarda los resultados y el puntaje
    session['results'] = results  # Opcional: guarda los resultados en la sesión si los necesitas en otra vista
    session['score'] = score

    # Llama a save_data_to_excel para guardar los resultados en el archivo
    save_data_to_excel(
        session['name'], session['surname'], session['age'], session['gender'], session['education'], quiz_results=results
    )

    # Retorna una página con el puntaje o redirige a otra ruta
    return render_template('quiz_results.html', score=score, total_questions=total_questions)


@app.route('/rate_humor_text', methods=['GET', 'POST'])
def rate_humor_text():
    if request.method == 'POST':
        session['humor_rating'] = request.form.get('rating')
        return redirect(url_for('text_preference_survey'))
    
    return render_template('rate_humor_text.html')


@app.route('/text_preference_survey', methods=['GET', 'POST'])
def text_preference_survey():
    if request.method == 'POST':
        session['preferred_text'] = request.form.get('preferred_text')
        return redirect(url_for('thank_you'))
    
    return render_template('text_preference_survey.html')



# Página final
@app.route('/final_page')
def final_page():
    return "¡Gracias por completar el proceso!"

if __name__ == '__main__':
    app.run(debug=True)
