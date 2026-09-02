def gerar_relatorio_completo(df, categoria, tipo='jogador'):
    texto = f"=== RELATÓRIO {categoria.upper()} ===\n"
    if tipo == 'jogador':
        texto += f"Total de jogadores: {len(df)}\n"
        if 'Idade' in df.columns and df['Idade'].notna().any():
            texto += f"Idade média: {df['Idade'].mean():.1f} anos\n"
        if 'IMC' in df.columns and df['IMC'].notna().any():
            texto += f"IMC médio: {df['IMC'].mean():.1f}\n"
        if 'Gordura_Corporal_%' in df.columns and df['Gordura_Corporal_%'].notna().any():
            texto += f"Gordura média: {df['Gordura_Corporal_%'].mean():.1f}%\n"
        if 'Rating_Geral_FM26' in df.columns and df['Rating_Geral_FM26'].notna().any():
            texto += f"Rating médio: {df['Rating_Geral_FM26'].mean():.1f}\n"
        if 'Posicao_Principal' in df.columns:
            texto += "\nDistribuição por posição:\n"
            for pos, qtd in df['Posicao_Principal'].value_counts().items():
                texto += f"  {pos}: {qtd}\n"
        if 'lesionado' in df.columns:
            qtd_les = df['lesionado'].sum()
            texto += f"\nJogadores lesionados: {qtd_les}\n"
    else:  # comissão
        texto += f"Total de membros: {len(df)}\n"
        if 'idade' in df.columns and df['idade'].notna().any():
            texto += f"Idade média: {df['idade'].mean():.1f} anos\n"
        if 'cargo' in df.columns:
            texto += "\nDistribuição por cargo:\n"
            for cargo, qtd in df['cargo'].value_counts().items():
                texto += f"  {cargo}: {qtd}\n"
    return texto