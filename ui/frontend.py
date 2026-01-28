from fasthtml.common import *
from monsterui.all import *
from functions.dine_funcs import *
import itsdangerous 
import qrcode

from functions.dash_funcs import *

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

@rt("/dine", methods=["GET", "POST"])
async def dine(request):
    # -------------------
    # GET → show the form
    # -------------------
    if request.method == "GET":
        return Container(
            H1("🍽️ Dine", cls="text-4xl font-bold text-center mb-6 mt-10"),
            Card(cls="p-8")(
                Form(
                    Input(
                        type="file",
                        accept="image/*",
                        name="photo",
                        required=True,
                        cls="mb-4"
                    ),
                    Input(
                        type="number",
                        name="no_in_party",
                        placeholder="Number of people in party",
                        required=True,
                        min="1",
                        cls="mb-4 w-full p-2 border rounded"
                    ),
                    Button("Upload Photo", type="submit", cls=f"{ButtonT.primary} w-full"),
                    method="post",
                    enctype="multipart/form-data"
                )
            ),
            cls=ContainerT.sm
        )

    # --------------------
    # POST → handle upload
    # --------------------
    form = await request.form()
    file = form.get("photo")
    no_in_party = form.get("no_in_party")

    if file is None or file.filename == "":
        return H2("No photo uploaded 😅")
    
    if not no_in_party or int(no_in_party) < 1:
        return H2("Please enter a valid number of people in party 😅")

    # Save uploaded image
    save_path = f"uploads/{file.filename}"
    contents = await file.read()

    with open(save_path, "wb") as f:
        f.write(contents)

    receipt_dict = parse_receipt(contents)
    receipt_dict["no_in_party"] = int(no_in_party)
    signed_token = generate_signed_qr_code(receipt_dict)
    
    qr = qrcode.QRCode()
    qr_code_link = f"http://localhost:5002/dinepay/{signed_token}"
    qr.add_data(qr_code_link)
    print(qr_code_link)
    qr.make()
    qr_img = qr.make_image()
    qr_img.save(f"uploads/qr_{file.filename}.png")

    return Container(
        H1("Receipt Received! ", cls="text-3xl font-bold text-center mt-10"),
        P(f"Send this code to whoever owes you money", cls="text-center mt-4"),
        Div(cls="flex flex-col items-center gap-6")(
            Img(src=f"/uploads/qr_{file.filename}.png", cls="w-64 h-64"),
        ),
        A(Button("Back to Home", cls=f"{ButtonT.secondary} mt-6"), href="/"),
        cls="text-center"
    )

@rt("/dinepay/{signed_token}", methods=["GET", "POST"])
async def dinepay(signed_token: str, request):
    # Read and validate the signed token
    try:
        auth_s = URLSafeSerializer("secret key", "auth")
        receipt_dict = auth_s.loads(signed_token)
        
    except Exception as e:
        return Container(
            H1("Invalid Token ❌", cls="text-3xl font-bold text-center mt-10"),
            P(f"Error: {str(e)}", cls="text-center mt-4"),
            A(Button("Back to Home", cls=f"{ButtonT.secondary} mt-6"), href="/"),
            cls="text-center"
        )
    
    # Handle POST request for calculation
    if request.method == "POST":
        form = await request.form()
        selected_indices = form.getlist("items")
        
        # Extract special fields
        tax = receipt_dict.get("tax", 0)
        tip = receipt_dict.get("tip", 0)
        other = receipt_dict.get("other", 0)
        no_in_party = receipt_dict.get("no_in_party", 1)
        
        # Extract items (everything except special fields)
        special_keys = {"tax", "tip", "other", "total", "no_in_party"}
        items = {k: v for k, v in receipt_dict.items() if k not in special_keys}
        items_list = list(items.items())
        
        # Calculate selected items total
        selected_items_total = 0
        selected_items_display = []
        for idx in selected_indices:
            if idx.isdigit() and int(idx) < len(items_list):
                item_name, item_price = items_list[int(idx)]
                selected_items_total += item_price
                selected_items_display.append((item_name, item_price))
        
        # Calculate per-person fees
        tax_per_person = tax / no_in_party if no_in_party > 0 else 0
        tip_per_person = tip / no_in_party if no_in_party > 0 else 0
        other_per_person = other / no_in_party if no_in_party > 0 else 0
        
        # Calculate final total
        final_total = selected_items_total + tax_per_person + tip_per_person + other_per_person
        
        return Container(
            H1("Payment Details", cls="text-3xl font-bold text-center mt-10"),
            
            Card(cls="p-8 mt-6")(
                H2("Your Share", cls="mb-4"),
                
                Div(cls="space-y-4 mb-6")(
                    H3("Selected Items:", cls="font-semibold mb-2"),
                    *[Div(cls="flex justify-between")(
                        Span(item_name, cls="text-gray-700"),
                        Span(f"${price:.2f}", cls="font-medium")
                    ) for item_name, price in selected_items_display]
                ),
                
                Div(cls="border-t pt-4 space-y-2")(
                    Div(cls="flex justify-between")(
                        Span("Tax (per person):", cls="font-semibold"),
                        Span(f"${tax_per_person:.2f}")
                    ),
                    Div(cls="flex justify-between")(
                        Span("Tip (per person):", cls="font-semibold"),
                        Span(f"${tip_per_person:.2f}")
                    ),
                    Div(cls="flex justify-between")(
                        Span("Other Fees (per person):", cls="font-semibold"),
                        Span(f"${other_per_person:.2f}")
                    ),
                    Div(cls="border-t pt-2 flex justify-between text-lg font-bold mt-4")(
                        Span("Your Total:"),
                        Span(f"${final_total:.2f}")
                    )
                )
            ),
            
            A(Button("Back to Home", cls=f"{ButtonT.secondary} mt-6"), href="/"),
            cls=f"{ContainerT.sm} text-center"
        )
    
    # Extract special fields
    tax = receipt_dict.get("tax", 0)
    tip = receipt_dict.get("tip", 0)
    other = receipt_dict.get("other", 0)
    no_in_party = receipt_dict.get("no_in_party", 1)
    
    # Extract items (everything except special fields)
    special_keys = {"tax", "tip", "other", "total", "no_in_party"}
    items = {k: v for k, v in receipt_dict.items() if k not in special_keys}
    
    # Calculate per-person fees
    tax_per_person = tax / no_in_party if no_in_party > 0 else 0
    tip_per_person = tip / no_in_party if no_in_party > 0 else 0
    other_per_person = other / no_in_party if no_in_party > 0 else 0
    
    # Create checkbox items
    checkbox_items = []
    items_list = list(items.items())
    for i, (item_name, price) in enumerate(items_list):
        checkbox_items.append(
            Div(cls="flex items-center mb-2")(
                Input(
                    type="checkbox",
                    name="items",
                    value=str(i),
                    id=f"item_{i}",
                    data_price=str(price),
                    onchange="updateTotal()",
                    cls="w-4 h-4 mr-3 item-checkbox"
                ),
                Label(
                    f"{item_name} - ${price:.2f}",
                    for_=f"item_{i}",
                    cls="cursor-pointer"
                )
            )
        )
    
    # Process the receipt data
    script_content = f"""
const taxPerPerson = {tax_per_person};
const tipPerPerson = {tip_per_person};
const otherPerPerson = {other_per_person};

function updateTotal() {{
    const checkboxes = document.querySelectorAll('.item-checkbox:checked');
    let itemsTotal = 0;
    
    checkboxes.forEach(checkbox => {{
        const price = parseFloat(checkbox.getAttribute('data-price'));
        itemsTotal += price;
    }});
    
    const total = itemsTotal + taxPerPerson + tipPerPerson + otherPerPerson;
    document.getElementById('total_display').textContent = '$' + total.toFixed(2);
}}

// Initialize total on page load
document.addEventListener('DOMContentLoaded', updateTotal);
"""
    
    # Process the receipt data - FastHTML supports returning lists of elements
    return [
        Container(
            H1("Payment Details", cls="text-3xl font-bold text-center mt-10"),
            
            Card(cls="p-8 mt-6")(
                H2("Select Items You Owe", cls="mb-4"),
                Form(
                    Div(cls="space-y-2")(*checkbox_items),
                    
                    Div(cls="border-t mt-6 pt-6 space-y-2")(
                        Div(cls="flex justify-between")(
                            Span("Tax (per person):", cls="font-semibold"),
                            Span(f"${tax_per_person:.2f}", id="tax_display")
                        ),
                        Div(cls="flex justify-between")(
                            Span("Tip (per person):", cls="font-semibold"),
                            Span(f"${tip_per_person:.2f}", id="tip_display")
                        ),
                        Div(cls="flex justify-between")(
                            Span("Other Fees (per person):", cls="font-semibold"),
                            Span(f"${other_per_person:.2f}", id="fees_display")
                        ),
                        Div(cls="border-t pt-2 flex justify-between text-lg font-bold mt-4")(
                            Span("Your Total:"),
                            Span("$0.00", id="total_display")
                        )
                    ),
                    
                    Button("Calculate My Share", type="submit", cls=f"{ButtonT.primary} w-full mt-6"),
                    method="post"
                )
            ),
            
            A(Button("Back to Home", cls=f"{ButtonT.secondary} mt-6"), href="/"),
            
            cls=f"{ContainerT.sm} text-center"
        ),
        Div(f'<script>{script_content}</script>')
    ]

@rt("/dash", methods=["POST"])
def dash_funcs():
    pass

serve(port=5002)
