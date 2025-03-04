from flask import Flask, request, send_from_directory, render_template, redirect, session, render_template, url_for
from flask_cors import CORS
from sqlalchemy.exc import IntegrityError
from flask_bcrypt import Bcrypt
from model import Session, Produto
from model.comentario import Comentario
from model.usuario import Usuario


app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

CORS(app)


@app.route('/')
def home():
    return render_template("home.html"), 200


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/x-icon')


@app.route('/add_produto', methods=['POST'])
def add_produto():
    session = Session()
    produto = Produto(
        nome=request.form.get("nome"),
        quantidade=request.form.get("quantidade"),
        valor=request.form.get("valor")
    )
    try:
        session.add(produto)
        session.commit()
        return render_template("produto.html", produto=produto), 200
    except IntegrityError as e:
        error_msg = "Produto de mesmo nome já salvo na base :/"
        return render_template("error.html", error_code=409, error_msg=error_msg), 409
    except Exception as e:
        error_msg = "Não foi possível salvar novo item :/"
        print(str(e))
        return render_template("error.html", error_code=400, error_msg=error_msg), 400


@app.route('/get_produto/<produto_id>', methods=['GET'])
def get_produto(produto_id):
    session = Session()
    produto = session.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        error_msg = "Produto não encontrado na base :/"
        return render_template("error.html", error_code= 404, error_msg=error_msg), 404
    else:
        return render_template("produto.html", produto=produto), 200


@app.route('/del_produto/<produto_id>', methods=['DELETE'])
def del_produto(produto_id):
    session = Session()
    count = session.query(Produto).filter(Produto.id == produto_id).delete()
    session.commit()
    if count ==1:
        return render_template("deletado.html", produto_id=produto_id), 200
    else: 
        error_msg = "Produto não encontrado na base :/"
        return render_template("error.html", error_code=404, error_msg=error_msg), 404


@app.route('/add_comentario/<produto_id>', methods=['POST'])
def add_comentario(produto_id):
    session = Session()
    produto = session.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        error_msg = "Produto não encontrado na base :/"
        return render_template("error.html", error_code= 404, error_msg=error_msg), 404

    autor = request.form.get("autor")
    texto = request.form.get("texto")
    n_estrelas = request.form.get("n_estrela")
    if n_estrelas:
        n_estrelas = int(n_estrelas)

    comentario = Comentario(autor, texto, n_estrelas)
    produto.adiciona_comentario(comentario)
    session.commit()
    return render_template("produto.html", produto=produto), 200

@app.route('/produtos', methods=['GET'])
def get_produtos():
    session = Session()
    produtos = session.query(Produto).all()
    produto_list = [
        {"nome": p.nome, "quantidade": p.quantidade, "valor": p.valor}
        for p in produtos
    ]
    return {"produtos": produto_list}, 200 

app.secret_key = "supersecretkey"  
bcrypt = Bcrypt(app)


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        if not nome or not email or not senha:
            return "Todos os campos são obrigatórios!", 400

        senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')

        session_db = Session()
        novo_usuario = Usuario(nome=nome, email=email, senha=senha_hash)

        try:
            session_db.add(novo_usuario)
            session_db.commit()
            return redirect(url_for('login')) 
        except IntegrityError:
            session_db.rollback()
            return "Email já cadastrado!", 400
        except Exception as e:
            return f"Erro inesperado: {str(e)}", 500 

    return render_template('cadastro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        session_db = Session()
        usuario = session_db.query(Usuario).filter_by(email=email).first()

        if usuario and bcrypt.check_password_hash(usuario.senha, senha):
            session['usuario_id'] = usuario.id
            session['usuario_nome'] = usuario.nome
            return redirect(url_for('home'))
        else:
            return "Email ou senha incorretos!", 401

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
