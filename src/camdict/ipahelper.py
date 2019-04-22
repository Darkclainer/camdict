'''A few function to convert latin character to they superscript and subscript equvivalence'''
script_to_superscript = {
    'a':'ᵃ',
    'b':'ᵇ',
    'c':'ᶜ',
    'd':'ᵈ',
    'e':'ᵉ',
    'f':'ᶠ',
    'g':'ᵍ',
    'h':'ʰ',
    'i':'ⁱ',
    'j':'ʲ',
    'k':'ᵏ',
    'l':'ˡ',
    'm':'ᵐ',
    'n':'ⁿ',
    'o':'ᵒ',
    'p':'ᵖ',
    'r':'ʳ',
    's':'ˢ',
    't':'ᵗ',
    'u':'ᵘ',
    'v':'ᵛ',
    'w':'ʷ',
    'x':'ˣ',
    'y':'ʸ',
    'z':'ᶻ',
    'ə':'ᵊ'
}

script_to_subscript = { 
    'a':'ₐ',
    'e':'ₑ',
    'h':'ₕ',
    'i':'ᵢ',
    'j':'ⱼ',
    'k':'ₖ',
    'l':'ₗ',
    'm':'ₘ',
    'n':'ₙ',
    'o':'ₒ',
    'p':'ₚ',
    'r':'ᵣ',
    's':'ₛ',
    't':'ₜ',
    'u':'ᵤ',
    'v':'ᵥ',
    'x':'ₓ'
}

def superscript(sequence):
    return ''.join(script_to_superscript[c] for c in sequence)

def subscript(sequence):
    return ''.join(script_to_subscript[c] for c in sequence)
