#!/bin/bash

#01. Atualiza data da rodada
python 01_data_rodada.py

#02. Faz a coleta da precipitação operacional para postos selecionados
python 02_precipitacao_postos.py

#03. Realiza a espacialização da precipitação coletada, união com histórico
#   e regionalização por sub-bacia
python 03_espacializa_precipitacao.py
