// Configuração do estúdio vista pelo painel. Vem do ambiente (painel/web/.env.local — modelo em .env.example na raiz):
//   NEXT_PUBLIC_CONTA_INSTAGRAM  o @ da conta que o estúdio publica (aparece na barra lateral e no rodapé)
//   NEXT_PUBLIC_TZ_PUBLICACAO    o fuso em que os posts são agendados — o mesmo TZ_PUBLICACAO do scripts/publicar.py
export const CONTA = process.env.NEXT_PUBLIC_CONTA_INSTAGRAM || "@sua_conta";
export const FUSO = process.env.NEXT_PUBLIC_TZ_PUBLICACAO || "UTC";
