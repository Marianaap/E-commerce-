from os import add_dll_directory
import re
from flask import *
import sqlite3
import itertools
from datetime import date,datetime,time


app = Flask(__name__)
app.secret_key = 'MRP'


@app.route('/pedidos/<float:total>')
def pedidos(total):
    
    now = datetime.now()
    
    data = str(date(day = now.day, month = now.month, year = now.year))
    hora = str(time(hour=now.hour, minute=now.minute))
    formadepagamento = ("credito")
    usuario_logado = session['usuario_logado']

    print(data,hora,formadepagamento,usuario_logado,total)

    con = sqlite3.connect('banco.db')
    
    con.execute("INSERT INTO Orders (Valor, Data, Horario, Pagamento, Email) VALUES (?,?,?,?,?) ", (total , data , hora , formadepagamento , usuario_logado))
    con.commit()
    con.close()

    return redirect('/')

@app.route('/minhaconta')
def minhaconta():
    con = sqlite3.connect('banco.db')
    cur = con.cursor()
    usuario_logado = session['usuario_logado']
    nome_usuario = cur.execute("SELECT nome FROM Cliente where email = '" + usuario_logado +"'").fetchone()[0]
    flash('Olá, ' + nome_usuario + '')
    return render_template ('Minhaconta.html')


@app.route('/meuspedidos')
def meuspedidos():
    if 'usuario_logado' not in session or session['usuario_logado'] == None:
        return redirect('/login')
    
    con = sqlite3.connect('banco.db')
    cur = con.cursor()
    usuario_logado = session['usuario_logado']

    pedidos = cur.execute("SELECT ID_Pedidos,Valor,Data,Horario,Pagamento,Email FROM Orders where Email = '" + usuario_logado +"'").fetchall()
    con.close()
    
    return render_template ('MeusPedidos.html', pedidos = pedidos)


@app.route('/deletar/<int:id>')
def deletar(id):
    
    con = sqlite3.connect('banco.db')

    con.execute("delete from Shopping_Cart where ID_Cart = ?",(id,))
    con.commit()

    con.close()

    return redirect('/carrinho')

@app.route('/pagando')
def pagando():

    usuario_logado = session['usuario_logado']

    con = sqlite3.connect('banco.db')
    cur = con.cursor()

    produtos_carrinho = cur.execute("SELECT Valor FROM Shopping_Cart where email = '" + usuario_logado +"'").fetchall()

    total = 0

    for tota in produtos_carrinho:
        subtotal = tota[0]
        total = total + subtotal

    pagamentosregistrados = cur.execute("SELECT Nomec, Numero FROM payment where email = '" + usuario_logado +"'").fetchall()


    con.close()

    return render_template ('cartao.html', total = total, registrados = pagamentosregistrados)



@app.route('/carrinho')
def carrinho():
    
    if 'usuario_logado' not in session or session['usuario_logado'] == None:
        return redirect('/login')
    
    usuario_logado = session['usuario_logado']
    
    con = sqlite3.connect('banco.db')
    cur = con.cursor()
    
    produtos_carrinho = cur.execute("SELECT Nome,Valor,Imagem,ID_Cart FROM Shopping_Cart where email = '" + usuario_logado +"'").fetchall()
    
    total = 0

    for tota in produtos_carrinho:
        subtotal = tota[1]
        total = total + subtotal
     

    con.close()

    return render_template ('Carrinho.html',titulo='Produtos', produtos = produtos_carrinho, total = total)

@app.route('/adicionar/<int:id>')
def adicionar(id):
    usuario_logado = session['usuario_logado']

    if 'usuario_logado' not in session or session['usuario_logado'] == None:
        return redirect('/login')

    con = sqlite3.connect('banco.db')
    cur = con.cursor()

    Nome = cur.execute("SELECT Nome FROM livros where ID_Livros = ?",(id,)).fetchone()[0]
    Valor = cur.execute("SELECT Valor FROM livros where ID_Livros = ?",(id,)).fetchone()[0]
    Imagem = cur.execute("SELECT Fotos FROM livros where ID_Livros = ?",(id,)).fetchone()[0]
    

    cur.execute("INSERT INTO Shopping_Cart (Nome,Valor,Imagem,Email) VALUES (?,?,?,?) " ,(Nome,Valor,Imagem,usuario_logado))
    con.commit()

    con.close()

    return redirect('/')


#telas

@app.route('/descricao/<int:id>')
def descricao(id):

    con = sqlite3.connect('banco.db')
    cur = con.cursor()

    produtos = cur.execute("SELECT Nome,Valor,Fotos,Descricao FROM livros where ID_Livros = ?",(id,)).fetchone()
    
    
    con.close()

    return render_template('produtodescricao.html', produtos = produtos)

@app.route('/')
def principal():
    if 'usuario_logado' not in session or session['usuario_logado'] != None:
        return redirect('logado')

    con = sqlite3.connect('banco.db')
    cur = con.cursor()

    produtos = cur.execute("SELECT Nome,Valor,Fotos,ID_Livros FROM Livros ").fetchall()[0:6]
    
    con.close()

    return render_template('Telamenupro.html', produtos = produtos)

@app.route('/logado')
def logado():
    if 'usuario_logado' not in session or session['usuario_logado'] == None:
        return redirect('/')

    con = sqlite3.connect('banco.db')
    cur = con.cursor()
    usuario_logado = session['usuario_logado']
    produtos = cur.execute("SELECT Nome,Valor,Fotos,ID_Livros FROM Livros ").fetchall()[0:6]
    nome_usuario = cur.execute("SELECT nome FROM Cliente where email = '" + usuario_logado +"'").fetchone()[0]
    flash('Olá, ' + nome_usuario + '')
    con.close()

    return render_template('TelamenuproLogada.html',produtos = produtos)


@app.route('/login')
def login():
    return render_template('TelaLogin.html')

@app.route('/autenticar', methods=['POST',])
def autenticar():
    senha = request.form['senha']
    email =  request.form['email']

    con = sqlite3.connect('banco.db')
    cur = con.cursor()

    verificar = cur.execute("SELECT email FROM Cliente where email = '" + email +"'").fetchall()

    if verificar == [] :
        flash('Você ainda não é cliente, realize seu cadastro!')
        return redirect ('/login')
    else:
        
        cliente_senha = cur.execute("SELECT senha FROM Cliente where email = '" + email +"'").fetchone()[0]
        
            
        if cliente_senha != senha:
            return redirect ('/login')
        else:           
            if cliente_senha == senha:
                session ['usuario_logado'] = request.form['email']
                return redirect('/')
            else :
                flash('Dados errados, tente novamente!')
                return redirect ('/login')


@app.route('/logout')
def logout():
    session['usuario_logado'] = None
    flash('Usuário deslogado!')
    return redirect('/')

@app.route('/addnovoproduto',methods=['POST',])
def addnovoproduto():
    
    nome = request.form['nome']
    genero = request.form['genero']
    fotos = request.form['fotos']
    valor = request.form['valor']
    descricao = request.form['descricao'] 

    con = sqlite3.connect('banco.db')
    cur = con.cursor()

    cur.execute("INSERT INTO livros (Nome, Genero, Fotos, Valor, Descricao) VALUES (?,?,?,?) ", (nome , genero , fotos , valor, descricao))
    con.commit()

    con.close()

    return redirect('/')

@app.route('/cadastro')
def cadastro():
    return render_template('TelaCadastro.html')

@app.route('/cadastrando',methods=['POST',])
def cadastrando():
    
    nome = request.form['nome']
    email = request.form['email']
    senha = request.form['senha']
    cpf = request.form['cpf']
    cep = request.form['cep'] 
    endereco = request.form['endereco']
    bairro = request.form['bairro']
    numero = request.form['numero']
    complemento = request.form['complemento']
    cidade = request.form['cidade']

    con = sqlite3.connect('banco.db')
    cur = con.cursor()

    cur.execute("INSERT INTO Cliente (Nome, Email, Senha, CPF) VALUES (?,?,?,?) ", (nome , email , senha , cpf))
    cur.execute("INSERT INTO Endereco (CEP, Endereco, Numero, Complemento, Bairro, Cidade) VALUES (?,?,?,?,?,?) ", (cep , endereco , numero , complemento, bairro, cidade))
    con.commit()

    con.close()

    return redirect('/')

@app.route('/produtos')
def produto():
    
    con = sqlite3.connect('banco.db')
    cur = con.cursor()

    produtos = cur.execute("SELECT Nome,Valor,Fotos FROM Livros ").fetchall()

    con.close()

    return render_template('produtos.html',produtos = produtos)

@app.route('/terror')
def terror():
    
    con = sqlite3.connect('banco.db')
    cur = con.cursor()
    
    produtos = cur.execute("SELECT Nome,Valor,Fotos FROM Livros where Genero = 'terror' ").fetchall()

    con.close()

    return render_template('terror.html',produtos = produtos)

@app.route('/aventura')
def aventura():
    
    con = sqlite3.connect('banco.db')
    cur = con.cursor()

    produtos = cur.execute("SELECT Nome,Valor,Fotos FROM Livros where Genero = 'aventura' ").fetchall()

    con.close()

    return render_template('aventura.html',produtos = produtos)

@app.route('/programacao')
def programacao():
    
    con = sqlite3.connect('banco.db')
    cur = con.cursor()

    produtos = cur.execute("SELECT Nome,Valor,Fotos FROM Livros where Genero = 'programacao' ").fetchall()

    con.close()

    return render_template('programacao.html',produtos = produtos)

@app.route('/medicina')
def medicina():
    
    con = sqlite3.connect('banco.db')
    cur = con.cursor()

    produtos = cur.execute("SELECT Nome,Valor,Fotos FROM Livros where Genero = 'medicina' ").fetchall()

    con.close()

    return render_template('medicina.html',produtos = produtos)

@app.route('/advocacia')
def advogacia():
    
    con = sqlite3.connect('banco.db')
    cur = con.cursor()

    produtos = cur.execute("SELECT Nome,Valor,Fotos FROM Livros where Genero = 'advocacia' ").fetchall()

    con.close()

    return render_template('advocacia.html',produtos = produtos)




app.run(debug=True)