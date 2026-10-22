import json, subprocess, cv2, numpy as np, os, shutil
OUT = r'C:\Users\mathe\Skills\_research\mc-test'
os.chdir(os.path.join(OUT, 'out'))
plan = json.load(open('../work/plan.json', encoding='utf8'))
rend = json.load(open('v11.json', encoding='utf8'))
SRC = []
for i in (1, 2):
    for w in json.load(open(f'../work/t{i}.json', encoding='utf8'))['words']: SRC.append((w['s'], f't{i}', w['w'].strip()))
SRC.sort()
fmt = lambda t: '%d:%05.2f' % (t // 60, t % 60)
shutil.rmtree('../judge_pack', ignore_errors=True); os.makedirs('../judge_pack')
L = ['# Pacote do juiz — Teste 8min Problems (v11, após a 3ª rodada de juízes: 7, 8, 6, 7)', '',
     'Vídeo: bruto POV Minecraft (canal Problems), primeiros 8 min (480 s fonte) -> 439.5 s editados. Render do Premiere (exportAsMediaDirect): out/teste8min_v11.mp4. Você NÃO ouve/assiste o vídeo; julgue pelas evidências abaixo.', '',
     '## Métricas medidas no render (ffmpeg ebur128 + amostras + separação de stems demucs)',
     '- Loudness integrado -15.9 LUFS (dentro de -14 a -16), LRA 3.5 LU. TRUE PEAK -0.9 dBTP (ebur128 peak=true); pico de amostra -0.97 dBFS, 0 amostras >0.95 (sem clipping). Para um export final no YouTube um teto de -1 dBTP é o usual: -0.9 está 0.1 dB acima disso (diferença desprezível; o editor pode pôr um limitador de master a -1 dBTP no export).',
     '- Cadeia: nas 3 faixas do bruto, +9 dB de ganho antes do "Limitador pesado" do Premiere (limiar 0.91; escolhido por teste: 0.90 -> -18.0 LUFS/pico -3.7; 0.93 -> -16.2 LUFS/pico -1.0, mas clipava com duas vozes gritando; 0.97 sem efeito); música/SFX com +3 dB. LRA 3.5 LU indica voz comprimida (as referências do canal têm LRA 1.7–2.7 LU), não há medida de gain reduction nem de distorção do limitador (não ouço).',
     '- Proporção medida por stems (demucs) no render: voz em mediana 14.2 dB acima de (música+jogo+SFX) por janela de 10 s (p10 10.8, p90 20.4); alvo da régua ~15 dB. Incerteza: separação por stems não é perfeita e mistura música, jogo e SFX; vazamento de voz para os outros stems tende a SUBESTIMAR a diferença.',
     '- Níveis por faixa de música: cada faixa foi igualada pelo seu LUFS integrado de arquivo para -31 LUFS (ganho = -31 - LUFS_arquivo + 3 dB), por isso os ganhos em dB diferem entre faixas (as faixas Epidemic vêm masterizadas de -7 a -17 LUFS); a igualação é por LUFS integrado, não por percepção.',
     '- SFX nivelados p/ ~-23 LUFS integrado (+3 dB geral); SFX com pico alto no arquivo (dun-dun-dun, rimshot) receberam -4 dB extra. Duck da música -9 dB por 1 s nos SFX de piada (parâmetro; não medido por evento).',
     '- Buracos: o script fecha buracos entre clipes em V1/A1/A2/A3. Música: fade-in 0.08 s / fade-out 0.12 s; 9 faixas de 34–79 s (régua: 30 s–1:30). O silêncio exato nas emendas de música não foi medido.',
     '- Alinhamento SFX×palavra: o tempo de cada SFX vem da palavra-âncora no ASR POR PALAVRA do bruto (campo "bruto" abaixo, tempo de fonte). O campo "render" mostra as palavras que o ASR leu no render naquele instante: o ASR pode ler outra palavra por causa da sobreposição de vozes (ex.: "bugou" lido como "boboias"), então "render" é só conferência de ordem de grandeza.', '',
     '## Estrutura no Premiere (nada mesclado, tudo editável/restaurável)',
     '- Projeto: D:\\Pobrs\\Teste Problems.prproj (cópia de segurança antes de editar: "Teste Problems.backup-pre-edicao.prproj"). Sequência de trabalho "TESTE 8min - Problems v11" (clone limpo da original); "Sequência 01 (original)" intacta com o bruto inteiro. Sequências de tentativas anteriores continuam no projeto com nome "(v10)", "(v11 incompleta)", "(descartada)".',
     '- Enquadramento: bruto 3840x1080 60 fps com o jogo na METADE DIREITA (esquerda preta). Em V1: Movimento > Posição [0, 0.5] (coordenadas normalizadas; x=0 leva o centro do bruto à borda esquerda do quadro), Escala 100 => a metade direita do bruto preenche 1920x1080 (verificado nos frames). Nos zooms o foco é dado em px do quadro 1920x1080 e convertido para Posição normalizada.',
     '- V1 = bruto em 19 clipes cortados (Posição/Escala keyframeadas nos zooms; Distorção de lente keyframeada nos gags da barriga). V2 = sticker "?". A1 = voz principal (POV), A2 = amigos em call (personagens do roteiro), A3 = som do jogo (separadas; Limitador pesado por clipe, 57 no total), A4 = música, A5 = SFX.',
     '- Zooms ancorados num ponto de foco (o ponto fica parado; nada expõe borda preta).', '',
     '## O que mudou desde a 3ª rodada (juízes: 7 ritmo/cortes, 8 música [aprovou], 6 SFX/zoom, 7 mixagem)',
     '- Densidade: 20 SFX (14 arquivos distintos) e 19 zooms + 2 stickers em 439 s (antes 17 e 13). Novos efeitos nos buracos que o juiz apontou: 40–99 s (punch+bonk em "Essa poça aqui é minha", punch+rimshot em "Quem esvaziar primeiro ganha", punch em "Bora, bora, bora" fechando o gancho), 131–211 s (trombone triste na reprise do 0,1%, whoosh+punch em "Vamos dar uma procurada na vila", sticker "?" em "beber água da plantação?"), 218–299 s (vine+punch em "É um canudo gigante", bonk+punch em "é muito devagar"). Whoosh reduzido de 4 para 2 usos; mais variedade (bonk, rimshot, trombone).',
     '- Mixagem: de -16.9 para -15.9 LUFS (dentro do alvo), true peak -0.9 dBTP medido.',
     '- Marcadores novos: possíveis retakes que o juiz citou ("bochecha dele" ×2, "isso aqui é músculo" ×2, "vamos beber junto com o patrão do poço d água" ×2, "vamos beber a água da plantação" ×2, "bora continuar bebendo") — NÃO cortei porque são falas curtas de t1/t2 sobrepostas no ASR e cortar arrisca perder fala do roteiro; e 3 marcadores nos ~2 s sem fala do ASR (32.8, 203.8, 391.5 na timeline) p/ o editor decidir ouvindo. Marcador do final reescrito (o ASR lê "não tá bugado nada" de forma variável por sobreposição com "R$ 1.500,00, Vitor").',
     '- Telas pretas de passagem de ato (padrão §3: ~1 s + silêncio a cada ~3 min nas referências): NÃO adicionadas neste teste porque o trecho é de 8 min dentro de um vídeo de 36 min e o editor decide os atos; as viradas de cena aqui são marcadas por troca de música.',
     '- Causa do "estado de áudio corrompido" da sequência anterior: desconhecida (a sequência passou a exportar -20 dB fixos depois de muitos testes de efeito de áudio; uma cópia limpa da original resolveu). Por isso cada versão é montada numa CLONE nova.', '', '## Cortes (tempos de FONTE em s)']
for c in plan['cuts']: L.append(f"- {c['a']:.2f}–{c['b']:.2f} ({c['b']-c['a']:.1f}s): {c['why']}")
L += ['', '## Música (Epidemic Sound; tempos na TIMELINE final)']
for m in plan['music']:
    L.append(f"- {fmt(m['tl_in'])}–{fmt(m['tl_out'])} ({m['tl_out']-m['tl_in']:.0f}s): {os.path.basename(m['file'])} — {m['why']} (ganho {m['gain_db']+plan['boost_music_db']:+.1f} dB)")
L += ['', '## SFX: tempo na timeline | palavra-âncora no bruto (ASR por palavra, tempo de fonte) | palavras lidas no render (ASR, pode errar)']
Wd = rend['words']
for s in plan['sfx']:
    near_r = ' '.join(w['w'].strip() for w in Wd if s['tl'] - 1.2 <= w['s'] <= s['tl'] + 1.5)
    near_s = ' '.join(f"{w[2]}:{w[0]:.1f}" for w in SRC if s['src'] - 0.8 <= w[0] <= s['src'] + 0.3)
    near_s2 = ' '.join(w[2] for w in SRC if s['src'] - 1.2 <= w[0] <= s['src'] + 0.3)
    L.append(f"- {fmt(s['tl'])}: {os.path.basename(s['file'])} — {s['why']} | bruto@{s['src']:.2f}s: \"{near_s2}\" | render: \"{near_r}\"")
L += ['', '## Zooms/efeitos visuais (tempo na timeline)']
for z in plan['zooms']:
    extra = (' + distorção de lente ' + str(z['curv'])) if 'curv' in z else ''
    L.append(f"- {fmt(z['tl'])}: {z['kind']} até {z['s']}% foco ({z.get('fx', 960)},{z.get('fy', 540)}) por ~{z['hold']}s{extra} — {z['why']}")
for s in plan['stickers']: L.append(f"- {fmt(s['tl'])}: sticker \"?\" (V2, pop de escala) por {s['dur']}s — {s['why']}")
L += ['', '## Marcadores REVISAR deixados na timeline para o editor humano']
for m in plan['marks']: L.append(f"- {fmt(m['tl'])}: {m['txt']}")
L += ['', '## Limitações conhecidas (declaradas)', '- Erros de fala detectados só por transcrição (ASR por palavra), sem ouvir; cliques/tosse NÃO tratados (marcado).',
      '- Trechos de fala sobreposta ilegíveis no ASR e possíveis retakes curtos ficaram marcados, não cortados (risco de cortar fala do roteiro).',
      '- Sem spotlight escuro nem glitch cromático nesta versão (distorção de lente sim).', '- O vídeo é um trecho de 8 min: termina no meio de uma cena (fim da janela de teste).', '',
      '## Referência de estilo', 'C:/Users/mathe/.claude/skills/minecraft-video-editor/references/padrao-edicao.md', '', '## Transcrição do render final (tempo = timeline)']
for s in rend['segments']: L.append(f"{fmt(s['s'])}–{fmt(s['e'])} {s['t']}")
open('../judge_pack/relatorio.md', 'w', encoding='utf8').write('\n'.join(L))


def frame(t, w):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{max(t, 0):.3f}', '-i', 'teste8min_v11.mp4', '-frames:v', '1', '-vf', f'scale={w}:-1', 'tmp.png'], check=True)
    im = cv2.imread('tmp.png'); cv2.putText(im, fmt(max(t, 0)), (6, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2); return im


n = int(439 // 15) + 1; ims = [frame(i * 15 + 1, 480) for i in range(n)]
while len(ims) % 3: ims.append(np.zeros_like(ims[0]))
rows = [np.hstack(ims[i:i + 3]) for i in range(0, len(ims), 3)]; h = len(rows) // 2
cv2.imwrite('../judge_pack/frames_a.jpg', np.vstack(rows[:h])); cv2.imwrite('../judge_pack/frames_b.jpg', np.vstack(rows[h:]))
rows = []
evs = sorted([(z['tl'], z['hold'], z['kind'] + ' ' + z['why'][:26]) for z in plan['zooms']] + [(s['tl'], s['dur'], 'sticker ?') for s in plan['stickers']])
for k in range(0, len(evs), 10):
    rows = []
    for t, H, why in evs[k:k + 10]:
        row = np.hstack([frame(x, 384) for x in [t - 0.3, t + 0.2, t + min(H, 1.2) * 0.7, t + H + 0.1, t + H + 0.8]])
        cv2.putText(row, why, (6, row.shape[0] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2); rows.append(row)
    cv2.imwrite(f'../judge_pack/efeitos_v11_{k // 10 + 1}.jpg', np.vstack(rows))
print('pack ok', len(L))
