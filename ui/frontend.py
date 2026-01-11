from fasthtml.common import *
from monsterui.all import *
# serve, Div, Span
# H1, H2, Card, Button, Form, Input, ButtonT, Container, ContainerT, Theme, fast_app
app, rt = fast_app(hdrs=Theme.blue.headers())

@rt
def index():

    return Container(
        H1("🍽️🏃 Dine-n-Dash", cls="text-4xl font-bold text-center mb-6 mt-10"),
        
        Card(cls="p-8 text-center")(
            H2("Are you dining or dashing today?", cls="mb-6"),
            
            # Use a vertical stack (flex-col)
            Div(cls="flex flex-col gap-4")(
                
                # Option 1: Using the standard A tag (requires fasthtml.common)
                A(Button("🍽️ Start Dine", cls=f"{ButtonT.primary} w-full h-16"), 
                  href="/dine"),
                
                # Option 2: If A is still failing, you can use the "Link" function
                # or just use a standard MonsterUI button with hx_get
                Button("🚗 Start Dash", 
                       cls=f"{ButtonT.secondary} w-full h-16",
                       hx_get="/dash", 
                       hx_target="body") 
            )
        ),
        cls=ContainerT.sm
    )

serve(port=5002) 


