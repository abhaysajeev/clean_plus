from ai4bharat.transliteration import XlitEngine

engine = XlitEngine("ml", beam_width=10, rescore=True)
out = engine.translit_word("Coimbatore Road", topk=3)
print(out["ml"])
