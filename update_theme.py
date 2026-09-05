import re

with open("src/App.tsx", "r") as f:
    content = f.read()

# Replace general light theme classes with premium dark theme
replacements = [
    # Global / Main background
    ('bg-gray-50', 'bg-[#0a0a0a] text-neutral-200'),
    ('border-gray-200', 'border-neutral-800'),
    
    # Sidebar
    ('bg-gray-50 p-4 border-r border-gray-200', 'bg-[#0a0a0a] p-4 border-r border-neutral-800'),
    ('text-indigo-700', 'text-indigo-400'),
    ('bg-indigo-50 text-indigo-700', 'bg-neutral-800 text-indigo-400'),
    ('text-gray-600 hover:bg-gray-100 hover:text-gray-900', 'text-neutral-400 hover:bg-neutral-800 hover:text-neutral-100'),
    
    # Cards
    ('bg-white rounded-lg shadow-sm border border-gray-100 text-indigo-600', 'bg-neutral-900 rounded-lg shadow-sm border border-neutral-800 text-indigo-400'),
    ('p-4 border border-gray-200 rounded-xl bg-gray-50', 'p-4 border border-neutral-800 rounded-xl bg-[#111111]'),
    ('text-gray-500', 'text-neutral-400'),
    
    # Inputs
    ('border p-2 rounded-lg flex-1', 'bg-neutral-900 border border-neutral-800 p-2 rounded-lg flex-1 text-neutral-200 placeholder-neutral-500 focus:outline-none focus:ring-1 focus:ring-indigo-500'),
    
    # List Items
    ('p-4 border rounded-lg flex justify-between items-center hover:shadow-sm', 'p-4 border border-neutral-800 bg-[#111111] rounded-lg flex justify-between items-center hover:border-neutral-700 transition-colors'),
    
    # Text colors
    ('text-gray-900', 'text-neutral-100'),
    
    # Primary Buttons
    ('bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700', 'bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-500 transition-colors font-medium'),
    
    # Links/Actions
    ('text-indigo-600 font-medium hover:underline', 'text-indigo-400 font-medium hover:text-indigo-300 transition-colors'),
    
    # Terminal area
    ('bg-gray-900 text-gray-100 p-4 rounded-xl overflow-auto font-mono text-sm space-y-2 border border-gray-800 shadow-inner', 'bg-[#050505] text-neutral-300 p-4 rounded-xl overflow-auto font-mono text-sm space-y-2 border border-neutral-800 shadow-inner'),
]

for old, new in replacements:
    content = content.replace(old, new)

# Fix double bg/text if any
content = content.replace('bg-[#0a0a0a] text-neutral-200 p-4 border-r', 'bg-[#0a0a0a] p-4 border-r')

with open("src/App.tsx", "w") as f:
    f.write(content)

