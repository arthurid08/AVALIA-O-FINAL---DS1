import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from app import db
from app.models import Produto, Categoria
main_bp = Blueprint('main', __name__)

EXTENSOES_PERMITIDAS = {'png', 'jpg', 'jpeg',}

def extensao_valida(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSOES_PERMITIDAS

def salvar_imagem(arquivo):
    ext = arquivo.filename.rsplit('.', 1)[1].lower()
    nome_unico = f"{uuid.uuid4().hex}.{ext}"
    caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], nome_unico)
    arquivo.save(caminho)
    return nome_unico

def remover_imagem_disco(nome_imagem):
    if nome_imagem and nome_imagem != 'padrao.png':
        caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], nome_imagem)
        if os.path.exists(caminho):
            os.remove(caminho)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    categorias = Categoria.query.order_by(Categoria.nome.asc()).all()

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        preco_raw = request.form.get('preco', '').replace(',', '.').strip()
        categoria_id = request.form.get('categoria_id')
        arquivo = request.files.get('imagem')

        if len(nome) < 3:
            flash('O nome do produto deve ter pelo menos 3 caracteres.', 'danger')
            return redirect(url_for('main.index'))

        try:
            preco = float(preco_raw)
        except ValueError:
            flash('Preço inválido. Informe um valor numérico.', 'danger')
            return redirect(url_for('main.index'))

        if preco <= 0:
            flash('O preço do produto deve ser maior que zero.', 'danger')
            return redirect(url_for('main.index'))

        if not categoria_id or not Categoria.query.get(categoria_id):
            flash('Selecione uma categoria válida.', 'danger')
            return redirect(url_for('main.index'))

        nome_imagem = 'padrao.png'
        if arquivo and arquivo.filename != '':
            if not extensao_valida(arquivo.filename):
                flash('Formato de imagem inválido! Aceitos: PNG, JPG, JPEG e WEBP.', 'danger')
                return redirect(url_for('main.index'))
            nome_imagem = salvar_imagem(arquivo)

        novo_produto = Produto(
            nome=nome,
            preco=preco,
            categoria_id=int(categoria_id),
            imagem=nome_imagem
        )
        db.session.add(novo_produto)
        db.session.commit()

        flash('Produto cadastrado com sucesso!', 'success')
        return redirect(url_for('main.index'))

    termo_busca = request.args.get('busca', '').strip()
    if termo_busca:
        produtos = Produto.query.filter(Produto.nome.ilike(f'%{termo_busca}%')).order_by(Produto.nome.asc()).all()
    else:
        produtos = Produto.query.order_by(Produto.nome.asc()).all()

    return render_template('index.html', produtos=produtos, categorias=categorias, busca=termo_busca)

@main_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    produto = Produto.query.get_or_404(id)
    categorias = Categoria.query.order_by(Categoria.nome.asc()).all()

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        preco_raw = request.form.get('preco', '').replace(',', '.').strip()
        categoria_id = request.form.get('categoria_id')
        arquivo = request.files.get('imagem')

        if len(nome) < 3:
            flash('O nome do produto deve ter pelo menos 3 caracteres.', 'danger')
            return redirect(url_for('main.editar', id=produto.id))

        try:
            preco = float(preco_raw)
        except ValueError:
            flash('Preço inválido. Informe um valor numérico.', 'danger')
            return redirect(url_for('main.editar', id=produto.id))

        if preco <= 0:
            flash('O preço do produto deve ser maior que zero.', 'danger')
            return redirect(url_for('main.editar', id=produto.id))

        if not categoria_id or not Categoria.query.get(categoria_id):
            flash('Selecione uma categoria válida.', 'danger')
            return redirect(url_for('main.editar', id=produto.id))

        if arquivo and arquivo.filename != '':
            if not extensao_valida(arquivo.filename):
                flash('Formato de imagem inválido! Aceitos: PNG, JPG, JPEG e WEBP.', 'danger')
                return redirect(url_for('main.editar', id=produto.id))
            
            remover_imagem_disco(produto.imagem)
            produto.imagem = salvar_imagem(arquivo)

        produto.nome = nome
        produto.preco = preco
        produto.categoria_id = int(categoria_id)

        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('main.index'))

    return render_template('editar.html', produto=produto, categorias=categorias)


@main_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir(id):
    produto = Produto.query.get_or_404(id)
    
    remover_imagem_disco(produto.imagem)
    
    db.session.delete(produto)
    db.session.commit()
    
    flash('Produto excluído com sucesso!', 'info')
    return redirect(url_for('main.index'))