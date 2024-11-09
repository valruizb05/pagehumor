from flask import Flask, request, render_template, redirect, url_for, session
import openai
import os
from dotenv import load_dotenv
import pandas as pd
import secrets

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

# Función para guardar los datos personales en Excel
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
            if quiz_results:
                for key, value in quiz_results.items():
                    df.at[row_index, key] = value
        else:
            df = pd.concat([df, pd.DataFrame(user_data)], ignore_index=True)
    else:
        df = pd.DataFrame(user_data)
    
    df.to_excel(file_path, index=False)

@app.route('/ask_topic', methods=['GET', 'POST'])
def ask_topic():
    if request.method == 'POST':
        category = request.form.get('category')
        session['category'] = category
        return redirect(url_for('show_texts_main', type="original"))  # Asegúrate de que el nombre del endpoint sea correcto
    return render_template('ask_topic.html')




@app.route('/show_texts/<type>', methods=['GET', 'POST'], endpoint='show_texts_main')
def show_texts_main(type):
    category = session.get('category')
    if category is None:
        return redirect(url_for('ask_topic'))  # Redirige a la página de selección si no hay categoría

    folder_path = os.path.join('data', type, category)
    
    if not os.path.exists(folder_path):
        return f"No se encontraron textos en la categoría {category}"

    texts = [f.replace('.txt', '') for f in os.listdir(folder_path) if f.endswith('.txt')]
    
    if request.method == 'POST':
        text = request.form.get('text')
        session['text'] = text
        return redirect(url_for('show_text_content', type=type))
    
    return render_template('show_texts.html', texts=texts, category=category, type=type)




@app.route('/show_text_content/<type>', methods=['GET', 'POST'], endpoint='show_text_content_main')
def show_text_content_main(type):
    category = session.get('category')
    text_file = session.get('text')
    folder_path = os.path.join('data', type, category)
    file_path = os.path.join(folder_path, f"{text_file}.txt")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    return render_template('show_texts_content.html', content=content, category=category, text_file=text_file)



@app.route('/quiz/<type>', methods=['GET', 'POST'])
def quiz(type):
    if request.method == 'POST':
        score = request.form.get('score')
        if type == "original":
            session['original_score'] = score
            return redirect(url_for('show_text_content', type="transformado"))  # Pasamos al texto humorístico
        else:
            session['humor_score'] = score
            return redirect(url_for('rate_humor_text'))  # Pasamos a la calificación de humor
    
    return render_template('quiz.html', type=type)



# Guardar resultados del cuestionario
@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    quiz_results = {
        'Resultado Quiz 1': request.form.get('quiz1'),
        'Resultado Quiz 2': request.form.get('quiz2')
    }
    save_data_to_excel(
        session['name'], session['surname'], session['age'], session['gender'], session['education'], quiz_results
    )
    return redirect(url_for('final_page'))

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
