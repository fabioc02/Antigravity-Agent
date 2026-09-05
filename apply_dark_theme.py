import re

with open("src/App.tsx", "r") as f:
    content = f.read()

replacements = {
    'bg-slate-50': 'bg-[#0a0a0a]',
    'bg-white': 'bg-[#111111]',
    'text-slate-800': 'text-neutral-200',
    'text-slate-900': 'text-neutral-100',
    'text-slate-500': 'text-neutral-400',
    'border-slate-200': 'border-neutral-800',
    'bg-slate-100': 'bg-neutral-800',
    'hover:bg-slate-100': 'hover:bg-neutral-800',
    'hover:text-slate-900': 'hover:text-neutral-100',
    'text-indigo-600': 'text-indigo-400',
    'hover:border-slate-300': 'hover:border-neutral-700',
    'bg-slate-900': 'bg-[#050505]',
    'text-slate-300': 'text-neutral-300',
    'placeholder-slate-400': 'placeholder-neutral-500'
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open("src/App.tsx", "w") as f:
    f.write(content)
