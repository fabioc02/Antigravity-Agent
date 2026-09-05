import re

with open("src/App.tsx", "r") as f:
    content = f.read()

replacements = {
    'bg-[#0a0a0a]': 'bg-slate-50',
    'bg-[#111111]': 'bg-white',
    'text-neutral-200': 'text-slate-800',
    'text-neutral-100': 'text-slate-900',
    'text-neutral-400': 'text-slate-500',
    'border-neutral-800': 'border-slate-200',
    'bg-neutral-800': 'bg-slate-100',
    'bg-neutral-900': 'bg-white',
    'hover:bg-neutral-800': 'hover:bg-slate-100',
    'hover:text-neutral-100': 'hover:text-slate-900',
    'text-indigo-400': 'text-indigo-600',
    'hover:border-neutral-700': 'hover:border-slate-300',
    'bg-[#050505]': 'bg-slate-900',
    'text-neutral-300': 'text-slate-300',
    'placeholder-neutral-500': 'placeholder-slate-400'
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open("src/App.tsx", "w") as f:
    f.write(content)
