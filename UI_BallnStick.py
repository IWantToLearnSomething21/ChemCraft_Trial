
#------------------------------- MODULES -----------------------------------------

from streamlit_option_menu import option_menu
import streamlit as st
import mysql.connector as my
import requests
import py3Dmol
import time as t
from rdkit import Chem
from rdkit.Chem import AllChem
import pandas as pd


#-------------------------------- FUNCTIONS ---------------------------------------

def initialisation():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.guest = False
        st.session_state.user = None
    if "guest_history" not in st.session_state:
        st.session_state.guest_history = []
        st.session_state.count=0
        print("---------------------------------------")


def update_page(x):
    if x==0:
        st.session_state.page="home"
    elif x==1:
        st.session_state.page="login"
    elif x==2:
        st.session_state.page="signup"

def update_accStatus(x):
    if x==0 :
        st.session_state.logged_in=True
    elif x==1:
        st.session_state.guest = True

def update_mainpage(x):
    if x==0:
        st.session_state.mainpage="new"
    elif x==1:
        st.session_state.mainpage="aboutus"
    elif x=="sidebar":
        st.session_state.mainpage="history"
    elif x=="sidebar_admin":
        st.session_state.mainpage="Admin_tables"
    elif x==2:
        st.session_state.mainpage="Admin"

def toggle_fhistory(x):
    if x==0:
        st.session_state.fhistory = False
    elif x==1:
        st.session_state.fhistory = True

def toggle_afhistory(x):
    if x==0:
        st.session_state.afhistory = False
    elif x==1:
        st.session_state.afhistory = True

def connection():
    con = my.connect(user = "root", host='localhost', passwd="Fanta@123",database="ChemCraft3")
    cur = con.cursor()
    return con,cur

def users():
    con,cur=connection()
    cur.execute("select username from users")
    l = [i[0] for i in cur.fetchall()]
    con.close()
    return l

def passwd_checker(u,p):#u - username; p - password
    con,cur=connection()
    cur.execute("select passwd from users where username='{}'".format(u))
    ap=cur.fetchone()[0]    # pa - actual password
    con.close()
    if ap==p:
        return True
    else:
        return False

def user_table_exists():
    if st.session_state.user.lower() in get_tables():
        return True
    else:
        return False

def is_admin():
    if st.session_state.user == "Administrator":
        return True
    return False

#-------------------------------------- SQL -------------------------------------------
def create_tables():
    con,cur = connection()
    if not con:
        return
    q1 = """
            CREATE TABLE IF NOT EXISTS users(
                userid INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE,
                passwd VARCHAR(255),
                email VARCHAR(100),
                typ VARCHAR(20)
            )
            """


    cur.execute(q1)
    con.commit()
    con.close()

def create_usertable(user):
    con,cur=connection()
    q="""create table %s(
       user varchar(40),
       searched varchar(100),
       smiles varchar(100)
       )"""%(user,)
    cur.execute(q)
    con.commit()
    con.close()

def get_userid(username):
    con, cur = connection()
    if not username:
        return None
    cur.execute("SELECT userid FROM users WHERE username='%s'"%(username,))
    result = cur.fetchone()
    con.close()
    return result[0]

def get_history(username,x):
    if not username:
        return []
    userid = get_userid(username)
    con, cur = connection()
    cur.execute("")
    col=["searched","smiles"]
    if not user_table_exists():
        return []
    if x==col[0]:
        cur.execute("SELECT searched FROM %s"%(username,))
    elif x==col[1]:
        cur.execute("SELECT searched FROM %s"%(username,))
    #cur.fetchone()
    result =cur.fetchall()
    con.close()
    # Convert string back to list
    if result:
        l= [i[0] for i in result]
        return l
    return []

def get_tables():
    q="show tables"
    con,cur=connection()
    cur.execute(q)
    r=cur.fetchall()
    con.close()
    l = [i[0] for i in r]
    return l

def update_history(iupac_input):
    smiles = iupac_to_smiles(iupac_input)
    if st.session_state.get("user") and smiles and smiles not in get_history(st.session_state.user,"smiles"):
        con, cur = connection()
        searched_str = get_history(st.session_state.user,"searched")
        smiles_str = get_history(st.session_state.user,"smiles")
        smiles_str.append(iupac_to_smiles(iupac_input))
        searched_str.append(iupac_input)
        if not user_table_exists():
            create_usertable(st.session_state.user)
        cur.execute("INSERT into %s values('%s','%s','%s')"%(st.session_state.user,st.session_state.user,iupac_input,smiles))
        con.commit()
        con.close()

#_____________________________________ Starting ________________________________________
def login():
    st.title("Welcome back to Chemcraft")
    st.header("Login")
    username = None

    with st.form(key='login'):
        user = st.text_input("**Username:**", placeholder="Username")
        passwd = st.text_input("**Password:**", placeholder="Password",type='password')
        if st.form_submit_button("Login"):
            if not user or not passwd:
                st.warning("Please enter both username and password")
            elif user not in users():
                st.error("User does not exist")
            elif not passwd_checker(user,passwd):
                st.error("Password is incorrect")
            else:
                st.success("Logged in successfully")
                st.balloons()
                update_accStatus(0)
                st.session_state.user = user
                st.session_state.page = "dashboard"
                start()
                #username = user
    st.button("Home",key='loginbutton',on_click=update_page,args=(0,))
     


def sign_up():
    st.title("Welcome to Chemcraft")
    st.header("Sign Up")
    username = None

    with st.form(key='sign up'):
        user = st.text_input("**Username:**", placeholder="Username")
        passwd = st.text_input("**Password:**", placeholder="Password",type='password')
        email = st.text_input("**Email:**", placeholder="Email")
        gender = st.radio("Gender", ["Male", "Female", "Other"])
        typ = st.selectbox("Who are you?", ("High school Student", "College Student", "Professor", "Enthusiast"))

        if st.form_submit_button("Sign Up"):
            if not user or not passwd or not email:
                st.warning("Please fill in all fields")
            elif user in users():
                st.error("Username already exists")
            else:
                con, cur = connection()
                if not con:
                    st.error("Cannot connect to database")
                    return None
                cur.execute(
                    "INSERT INTO users (username, passwd, email, typ) VALUES (%s, %s, %s, %s)",
                    (user, passwd, email, typ)
                )
                con.commit()
                st.success("Account created")
                st.balloons()
                update_accStatus(0)
                st.session_state.user = user
                st.session_state.page = "dashboard"
                start()
                # username = user
                con.close()
    st.button("Home",key='signup',on_click=update_page,args=(0,))
     

def home():
    st.title("Welcome to Chemcraft")
    with st.container(border=True):
        col=st.columns(3)
        with col[0]:
            st.button("Sign Up",use_container_width=True,on_click=update_page,args=(2,))
        with col[1]:
            st.button("Log in",use_container_width=True,on_click=update_page,args=(1,))
        with col[2]:
            st.button("Guest Mode",use_container_width=True,on_click=update_accStatus,args=(1,))

def guest_dashboard():
    st.title(" Guest Mode")
    st.info("You are exploring as a Guest. Sign up or log in to save your history and progress.")

    iupac_input = st.text_input("Enter IUPAC Name (Guest):")
    if iupac_input:
        rendering(iupac_input)
        st.session_state.guest_history.append(iupac_input)

    st.button("Return Home", on_click=update_page,args=(0,))

def display_table(q,x):
    con,cur=connection()
    if x==0:
        cur.execute("SELECT * FROM %s"%(q,))
    elif x==1:
        cur.execute(q)
    if cur.with_rows:
        rows=cur.fetchall()
        cols=[i[0] for i in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        st.table(df)

def admin_page():
    st.title("Admin Mode")
    q=st.text_input("Enter query:")
    display_table(q,1)



#_________________________________________ 3D Rendering __________________________________

def iupac_to_smiles(iupac_name):
    url = f"https://opsin.ch.cam.ac.uk/opsin/{iupac_name}.json"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json().get("smiles", None)
    else:
        return None


def fetch_3d_structure(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    mol = Chem.AddHs(mol)
    AllChem.EmbedMolecule(mol, AllChem.ETKDG())
    AllChem.MMFFOptimizeMolecule(mol)
    mol_block = Chem.MolToMolBlock(mol)
    return mol_block


def rendering(iupac_input):
    from rdkit.Chem import Descriptors, rdMolDescriptors
    ELEMENT_COLORS = {
        'C': 'gray', 'H': 'white', 'O': 'red', 'N': 'blue',
        'Cl': 'green', 'Fe': 'orange', 'S': 'yellow',
    }
    ELEMENT_NAMES = {
        'C': 'Carbon', 'H': 'Hydrogen', 'O': 'Oxygen', 'N': 'Nitrogen',
        'Cl': 'Chlorine', 'Fe': 'Iron', 'S': 'Sulfur',
    }

    if iupac_input:
        with st.spinner("Converting IUPAC to SMILES..."):
            smiles = iupac_to_smiles(iupac_input)
        if smiles:
            st.success(f"✅ SMILES: {smiles}")
            sdf_data = fetch_3d_structure(smiles)
            if sdf_data:
                mol = Chem.MolFromSmiles(smiles)
                present_atoms = set([atom.GetSymbol() for atom in mol.GetAtoms()])
                legend_html = "<div style='display:flex;flex-direction:column;align-items:flex-start;background:#fafaff;padding:6px 10px;border:1px solid #eee;border-radius:6px;width:135px;'>"
                legend_html += "<b>Color Reference</b>"
                for elem in present_atoms:
                    clr = ELEMENT_COLORS.get(elem, "lightgray")
                    name = ELEMENT_NAMES.get(elem, elem)
                    legend_html += f"""
                        <div title='{name}' style='margin:4px 0;cursor:pointer;display:flex;align-items:center;' 
                             onmouseover="highlightAtoms('{elem}')"
                             onmouseout="restoreAtoms('{elem}')"
                             onclick="highlightAtoms('{elem}')">
                            <span style='display:inline-block;width:15px;height:15px;margin-right:6px;background:{clr};
                              border-radius:4px;box-shadow:0 0 1px #aaa;border:1px solid #ccc;'></span>
                            <span style='font-size:13px;'>{elem} ({name})</span>
                        </div>
                    """
                legend_html += "</div>"
                js_sdf = sdf_data.replace("\n", "\\n").replace("'", "\\'")
                st.components.v1.html(f"""
                <html>
                <head>
                  <script src="https://3dmol.csb.pitt.edu/build/3Dmol-min.js"></script>
                </head>
                <body>
                  <div style="display:flex;flex-direction:row;">
                    <div id="viewer" style="width: 700px; height: 540px; margin-right:16px; border:1px solid #ccc;"></div>
                    {legend_html}
                  </div>
                  <script>
                    let viewer = $3Dmol.createViewer("viewer", {{ backgroundColor: "white" }});
                    var sdf = '{js_sdf}';
                    viewer.addModel(sdf, "mol");
                    viewer.setStyle({{
                      stick: {{ radius: 0.18, colorscheme: "element" }},
                      sphere: {{ scale: 0.3, colorscheme: "element" }}
                    }});
                    viewer.zoomTo();
                    viewer.render();

                    let highlightStyle = {{ sphere: {{ scale: 0.48, color: '#00FFFF' }}, stick: {{ color: '#00FFFF', radius:0.22 }} }};
                    function highlightAtoms(sym) {{
                        viewer.setStyle({{ elem: sym }}, highlightStyle);
                        viewer.render();
                    }}
                    function restoreAtoms(sym) {{
                        viewer.setStyle({{ elem: sym }}, 
                            {{ stick: {{ radius: 0.18, colorscheme: "element" }}, sphere: {{ scale: 0.3, colorscheme: "element" }} }}
                        );
                        viewer.render();
                    }}
                  </script>
                </body>
                </html>
                """, height=560)
                formula = rdMolDescriptors.CalcMolFormula(mol)
                mol_weight = rdMolDescriptors.CalcExactMolWt(mol)
                logp = Descriptors.MolLogP(mol)
                tpsa = rdMolDescriptors.CalcTPSA(mol)
                h_donors = rdMolDescriptors.CalcNumHBD(mol)
                h_acceptors = rdMolDescriptors.CalcNumHBA(mol)
                func_groups = []
                fg_smarts = {
                    'Alcohol (OH)': '[OX2H]',
                    'Amine (NH2)': '[NX3;H2,H1;!$(NC=O)]',
                    'Carboxylic Acid (COOH)': '[CX3](=O)[OX2H1]'
                }
                for name, smarts in fg_smarts.items():
                    patt = Chem.MolFromSmarts(smarts)
                    if mol.HasSubstructMatch(patt):
                        func_groups.append(name)
                if not func_groups:
                    func_groups.append("None detected")
                st.markdown(f"""
<style>
.info-card {{background:linear-gradient(105deg,#f9f6fd 60%,#e2ecfd 100%);
border-radius:15px;box-shadow:0 2px 12px #cce1f680;
padding:28px 34px 20px 34px;margin:28px auto 14px auto;
width:420px;font-family:'Segoe UI',Arial,sans-serif;border:2.5px solid #b9d0fa;}}
.info-section {{margin-bottom:18px;}}
.info-title {{font-size:1.4em;font-weight:800;
margin-bottom:8px;color:#3a46a5;letter-spacing:1px;}}
.info-icon {{font-size:1.24em;margin-right:8px;vertical-align:middle;}}
.info-key {{font-weight:700;color:#116980;margin-right:7px;font-size:1.05em;}}
.info-value {{color:#135cb7;font-size:1.13em;font-weight:600;}}
.functional-title {{font-size:1.18em;color:#d72631;font-weight:750;margin-bottom:10px;}}
.functional-item {{color:#178a3a;font-weight:700;font-size:1.05em;margin-bottom:2px;}}
</style>
<div class="info-card">
  <div class="info-section">
    <div class="info-title">🔬 Molecular Information</div>
    <div><span class="info-icon">🧪</span><span class="info-key">Formula:</span><span class="info-value">{formula}</span></div>
    <div><span class="info-icon">⚖</span><span class="info-key">Weight:</span><span class="info-value">{mol_weight:.2f} g/mol</span></div>
    <div><span class="info-icon">🌊</span><span class="info-key">LogP:</span><span class="info-value">{logp:.2f}</span></div>
    <div><span class="info-icon">🟦</span><span class="info-key">TPSA:</span><span class="info-value">{tpsa:.2f} Å²</span></div>
    <div><span class="info-icon">💧</span><span class="info-key">H-Bond Donors:</span><span class="info-value">{h_donors}</span></div>
    <div><span class="info-icon">💦</span><span class="info-key">H-Bond Acceptors:</span><span class="info-value">{h_acceptors}</span></div>
  </div>
  <div class="info-section">
    <span class="functional-title">🧩 Functional Groups Detected</span>
    {''.join([f'<div class="functional-item">{fg}</div>' for fg in func_groups])}
  </div>
</div>
""", unsafe_allow_html=True)
            else:
                st.error("❌ Could not generate 3D structure.")
        else:
            st.error("❌ Invalid IUPAC name.")


def fullrendering():
    st.title("🧪 3D Molecule Viewer")
    iupac_input = st.text_input("Enter IUPAC Name:")
    update_history(iupac_input)
    rendering(iupac_input)


#________________________________________ Side UI ________________________________________

def sidebar(username,typ):
    if username=="Administrator":
        with st.sidebar:
            st.button("Home", on_click=update_mainpage, args=(2,))
            if st.session_state.logged_in and is_admin():
                tables = get_tables()
            else:
                tables = None

            if tables:
                if "afhistory" not in st.session_state:
                    st.session_state.afhistory = False
                if "fhistory" not in st.session_state:
                    st.session_state.fhistory = False
                display_items = tables[-5:] if not st.session_state.afhistory else tables[::-1]
                option_menu(menu_title="Tables", options=display_items, key="sidebar_admin", on_change=update_mainpage)
                if len(tables) > 5:
                    if 'fhistory' in st.session_state and not st.session_state.fhistory:
                        st.button("More", key="more_btn", on_click=toggle_afhistory, args=(1,))
                    else:
                        st.button("Less", key="less_btn", on_click=toggle_afhistory, args=(0,))
    elif typ=="Civillian":
        with st.sidebar:
            st.button("New chat", on_click=update_mainpage, args=(0,))
            st.button("About Us", on_click=update_mainpage, args=(1,))
            searched_items = get_history(username,
                                         "searched") if st.session_state.logged_in else st.session_state.guest_history
            if searched_items:
                if "fhistory" not in st.session_state:
                    st.session_state.fhistory = False
                display_items = searched_items[-5:] if not st.session_state.fhistory else searched_items[::-1]
                option_menu(menu_title="History", options=display_items, key="sidebar", on_change=update_mainpage)
                if len(searched_items) > 5:
                    if not st.session_state.fhistory:
                        st.button("More", key="more_btn", on_click=toggle_fhistory, args=(1,))
                    else:
                        st.button("Less", key="less_btn", on_click=toggle_fhistory, args=(0,))

#------------------------------------------ ACTIONS ---------------------------------------



def start():
    print("Start",st.session_state.count)
    if not(st.session_state.logged_in or st.session_state.guest):
        if "page" not in st.session_state:
            if st.session_state.logged_in or st.session_state.guest:
                st.session_state.page = "dashboard"  # go straight to dashboard
            else:
                st.session_state.page = "home"  # login/signup
        if st.session_state.page == "home":
            home()
        elif st.session_state.page == "signup":
            sign_up()
        elif st.session_state.page == "login":
            login()
        if "user_history" not in st.session_state:
            st.session_state.user_history = []
    else:
        print("Else",st.session_state.count)
        st.rerun()


def page_main(): #s - selected
    username = st.session_state.user if not st.session_state.guest else None
    if is_admin():
        sidebar(username,"Admin")
    else:
        sidebar(username,"Civillian")
    if 'mainpage' not in st.session_state:
        if is_admin():
            st.session_state.mainpage = "Admin"
        else:
            st.session_state.mainpage = "new"
    if st.session_state.mainpage == "Admin":
        admin_page()
    elif st.session_state.mainpage == "new":
        fullrendering()
    elif st.session_state.mainpage == "aboutus":
        st.title("👩‍🔬 About Us")

        st.write("""
        Welcome to our **CHEMCRAFT**!  
        We are a team of Grade 12 students — **B C Prateek**, and **S Sai Pranav** — who share a passion for 
        combining science and technology.

        This website was developed as part of our Computer Science project.  
        It allows users to **visualize molecules in interactive 3D**, explore their **chemical properties**, and learn more about the 
        fascinating world of molecular structures.

        Our goal is to make chemistry more engaging and easier to understand through the power of code and visualization.
        """)

        st.subheader("🌟 Our Vision")
        st.write("""
        To bridge the gap between theory and visualization — helping learners truly see what molecules look like,  
        and how their structures define their behavior.
        """)

        st.subheader("💻 Technologies Used")
        st.write("""
        - **Python** for backend logic  
        - **Streamlit** for user interface  
        - **MySQL** for data management  
        - **3D molecular rendering tools** for visualization
        """)

        st.caption("© 2025 — Project by Prateek, Sanjai, and Pranav")

    elif st.session_state.mainpage == "history":
        rendering(st.session_state["sidebar"])
    elif st.session_state.mainpage == "Admin_tables":
        display_table(st.session_state["sidebar_admin"],0)

#------------------------------------------ EXECUTION -----------------------------------

create_tables()
initialisation()

def Main():
    if st.session_state.logged_in or st.session_state.guest:
        page_main()
    else:
        start()
    st.session_state.count += 1
    print("Main",st.session_state.count)


Main()
print("log", st.session_state.logged_in)
print("guest",st.session_state.guest)
print()
