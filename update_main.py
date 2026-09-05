import re

with open("src/App.tsx", "r") as f:
    content = f.read()

content = content.replace(
    'bg-white p-6 shadow-xl m-2 rounded-xl border border-gray-100',
    'bg-[#111111] p-6 shadow-xl m-2 rounded-xl border border-neutral-800'
)
content = content.replace(
    'text-neutral-200 text-neutral-100',
    'text-neutral-200'
)

with open("src/App.tsx", "w") as f:
    f.write(content)
