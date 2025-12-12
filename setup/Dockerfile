# アーキテクチャ対応のMiniconda3ベースイメージを使用（自動認識）
FROM continuumio/miniconda3:latest  
  
# 作業ディレクトリを設定  
WORKDIR /app  
  
# システムパッケージの更新とgitのインストール  
RUN apt-get update && apt-get install -y \  
    git \  
    curl \  
    && rm -rf /var/lib/apt/lists/*
  
# 環境構築ファイルをコピー
COPY setup/environment.yml /app/
COPY setup/customized_bio_env.yml /app/

# conda環境を作成してパッケージをインストール
RUN conda env create -f environment.yml && \
    conda run -n res-agent conda env update -f customized_bio_env.yml && \
    conda run -n res-agent pip install biomni --upgrade

# conda環境をアクティベート
SHELL ["conda", "run", "-n", "res-agent", "/bin/bash", "-c"]  
  
# データディレクトリを作成  
RUN mkdir -p /app/data  
  
# ポート8889を公開（Jupyter用）  
EXPOSE 8889  
  
# 環境変数を設定  
ENV CONDA_DEFAULT_ENV=res-agent 
ENV PATH=/opt/conda/envs/res-agent/bin:$PATH  
