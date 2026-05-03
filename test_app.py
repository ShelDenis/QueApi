import streamlit as st
import requests
import time
from PIL import Image
import io

API_URL = "http://localhost:8000"

st.set_page_config(page_title="QueLab", layout="wide")
st.title("📱 QueLab - Очереди для сдачи лаб")

# Инициализация
if "token" not in st.session_state:
    st.session_state.token = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "refresh_counter" not in st.session_state:
    st.session_state.refresh_counter = 0

def force_refresh():
    st.session_state.refresh_counter += 1
    st.rerun()

def safe_json(response):
    try:
        return response.json()
    except:
        return {"detail": response.text if response.text else "Неизвестная ошибка"}

# ==================== АВТОРИЗАЦИЯ ====================
with st.sidebar:
    st.header("🔐 Аккаунт")
    
    if st.session_state.token is None:
        tab1, tab2 = st.tabs(["Вход", "Регистрация"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Пароль", type="password")
                if st.form_submit_button("Войти"):
                    resp = requests.post(f"{API_URL}/login", json={"u_mail": email, "u_pswrd": password})
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.token = data["access_token"]
                        st.session_state.user_id = data["user_id"]
                        st.session_state.user_name = data["user_name"]
                        force_refresh()
                    else:
                        st.error("Ошибка входа")
        
        with tab2:
            with st.form("register_form"):
                name = st.text_input("Имя")
                surname = st.text_input("Фамилия")
                email = st.text_input("Email")
                password = st.text_input("Пароль", type="password")
                if st.form_submit_button("Зарегистрироваться"):
                    resp = requests.post(f"{API_URL}/register", json={
                        "u_name": name, "u_surname": surname, "u_mail": email, "u_pswrd": password
                    })
                    if resp.status_code == 200:
                        st.success("Регистрация успешна! Теперь войдите.")
                    else:
                        st.error("Ошибка регистрации")
    else:
        st.success(f"👋 {st.session_state.user_name}")
        if st.button("Выйти"):
            for key in ["token", "user_id", "user_name"]:
                st.session_state[key] = None
            force_refresh()

# ==================== ОСНОВНОЙ КОНТЕНТ ====================
if st.session_state.token is None:
    st.info("👈 Войдите или зарегистрируйтесь")
else:
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
    @st.cache_data(ttl=0, show_spinner=False)
    def load_all_queues(_headers):
        resp = requests.get(f"{API_URL}/queues", headers=_headers)
        if resp.status_code == 200:
            return resp.json()
        return []
    
    @st.cache_data(ttl=0, show_spinner=False)
    def load_my_queues(_headers, _user_id):
        resp = requests.get(f"{API_URL}/users/me/queues", headers=_headers)
        if resp.status_code == 200:
            return resp.json()
        return []
    
    @st.cache_data(ttl=0, show_spinner=False)
    def load_participants(_headers, queue_id):
        resp = requests.get(f"{API_URL}/queues/{queue_id}/participants", headers=_headers)
        if resp.status_code == 200:
            return resp.json()
        return []
    
    @st.cache_data(ttl=0, show_spinner=False)
    def load_queue_info(_headers, queue_id):
        resp = requests.get(f"{API_URL}/queues/{queue_id}", headers=_headers)
        if resp.status_code == 200:
            return resp.json()
        return None
    
    # 3 вкладки
    tab_create, tab_join, tab_chat = st.tabs(["➕ Создать очередь", "📋 Вступить в очередь", "💬 Чат"])
    
    # ========== ВКЛАДКА 1: СОЗДАНИЕ ==========
    with tab_create:
        st.subheader("Создание новой очереди")
        
        with st.form("create_form"):
            q_name = st.text_input("Название очереди")
            q_describe = st.text_area("Описание")
            submitted = st.form_submit_button("Создать")
            
            if submitted and q_name:
                resp = requests.post(
                    f"{API_URL}/queues",
                    json={"q_name": q_name, "q_describe": q_describe},
                    headers=headers
                )
                if resp.status_code == 200:
                    queue = resp.json()
                    st.success(f"✅ Очередь '{q_name}' создана! ID: {queue['q_id']}")
                    st.cache_data.clear()
                    time.sleep(1)
                    force_refresh()
                else:
                    error = safe_json(resp)
                    st.error(f"❌ {error.get('detail', 'Ошибка')}")
    
    # ========== ВКЛАДКА 2: ВСТУПЛЕНИЕ ==========
    with tab_join:
        st.subheader("Доступные очереди")
        
        all_queues = load_all_queues(headers)
        
        if not all_queues:
            st.info("Нет доступных очередей")
        else:
            for q in all_queues:
                # Получаем полную информацию об очереди (с аватаркой)
                queue_info = load_queue_info(headers, q['q_id'])
                avatar_url = f"{API_URL}{queue_info.get('q_img_path')}" if queue_info and queue_info.get('q_img_path') else None
                
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    # Рамка для аватарки
                    if avatar_url:
                        try:
                            st.image(avatar_url, width=80, caption="Аватар")
                        except:
                            st.image("https://placehold.co/80x80?text=No+Image", width=80)
                    else:
                        st.image("https://placehold.co/80x80?text=Queue", width=80)
                
                with col2:
                    st.write(f"**{q['q_name']}**")
                    st.write(f"👥 {q['participants_count']} чел.")
                    st.caption(q.get('q_describe', 'Нет описания')[:100])
                    
                    if st.button("➕ Вступить", key=f"join_btn_{q['q_id']}"):
                        resp = requests.post(f"{API_URL}/queues/{q['q_id']}/join", headers=headers)
                        if resp.status_code == 200:
                            st.success(f"✅ Вы вступили в очередь '{q['q_name']}'!")
                            st.cache_data.clear()
                            time.sleep(1)
                            force_refresh()
                        else:
                            error = safe_json(resp)
                            st.error(f"❌ {error.get('detail', 'Ошибка')}")
                
                st.divider()
    
    # ========== ВКЛАДКА 3: ЧАТ ==========
    with tab_chat:
        st.subheader("Мои очереди")
        
        my_queues = load_my_queues(headers, st.session_state.user_id)
        
        if not my_queues:
            st.info("Вы не состоите ни в одной очереди")
        else:
            # Выбор очереди
            queue_options = {f"{q['q_name']} (ID: {q['q_id']})": q for q in my_queues}
            selected_name = st.selectbox("Выберите очередь", list(queue_options.keys()))
            selected_queue = queue_options[selected_name]
            
            # Загружаем полную информацию
            queue_info = load_queue_info(headers, selected_queue['q_id'])
            avatar_url = f"{API_URL}{queue_info.get('q_img_path')}" if queue_info and queue_info.get('q_img_path') else None
            
            # Заголовок с аватаркой и названием
            col1, col2 = st.columns([1, 3])
            
            with col1:
                # Рамка для аватарки
                if avatar_url:
                    try:
                        st.image(avatar_url, width=100)
                    except:
                        st.image("https://placehold.co/100x100?text=Queue", width=100)
                else:
                    st.image("https://placehold.co/100x100?text=Queue", width=100)
            
            with col2:
                st.write(f"## {selected_queue['q_name']}")
                st.caption(selected_queue.get('q_describe', 'Нет описания'))
            
            # Загрузка аватарки (только для создателя)
            if selected_queue.get('is_creator'):
                st.divider()
                st.write("**📸 Изменить аватарку очереди:**")
                uploaded_file = st.file_uploader(
                    "Выберите изображение",
                    type=["jpg", "jpeg", "png", "gif", "webp"],
                    key=f"avatar_upload_{selected_queue['q_id']}"
                )
                
                if uploaded_file is not None:
                    # Показываем预览
                    st.image(uploaded_file, width=150, caption="Новая аватарка")
                    
                    if st.button("Сохранить аватарку", key="save_avatar"):
                        files = {"file": uploaded_file}
                        resp = requests.post(
                            f"{API_URL}/queues/{selected_queue['q_id']}/upload-avatar",
                            headers=headers,
                            files=files
                        )
                        if resp.status_code == 200:
                            st.success("✅ Аватарка загружена!")
                            st.cache_data.clear()
                            time.sleep(1)
                            force_refresh()
                        else:
                            error = safe_json(resp)
                            st.error(f"❌ {error.get('detail', 'Ошибка')}")
            
            st.divider()
            
            # Список участников
            participants = load_participants(headers, selected_queue['q_id'])
            participants_count = len([p for p in participants if p['position'] > 0])
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.metric("👥 Участников", participants_count)
                if selected_queue.get('your_position'):
                    st.metric("📍 Ваша позиция", selected_queue['your_position'])
                elif selected_queue.get('is_creator'):
                    st.write("👑 Вы создатель")
            
            with col2:
                st.write("**Очередь:**")
                if not participants:
                    st.write("Пусто")
                else:
                    for p in participants:
                        if p['position'] == 0:
                            st.write(f"   👑 {p['user_name']}")
                        else:
                            current_mark = " ← ВЫ" if p['user_id'] == st.session_state.user_id else ""
                            st.write(f"   {p['position']}. {p['user_name']}{current_mark}")
            
            # Кнопки действий
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                if st.button("🚪 Выйти из очереди"):
                    resp = requests.post(f"{API_URL}/queues/{selected_queue['q_id']}/leave", headers=headers)
                    if resp.status_code == 200:
                        st.success("✅ Вы вышли из очереди")
                        st.cache_data.clear()
                        time.sleep(1)
                        force_refresh()
                    else:
                        error = safe_json(resp)
                        st.error(f"❌ {error.get('detail', 'Ошибка')}")
            with col_btn2:
                if st.button("🔄 Встать в конец"):
                    resp = requests.post(f"{API_URL}/queues/{selected_queue['q_id']}/rejoin", headers=headers)
                    if resp.status_code == 200:
                        st.success("✅ Перемещены в конец")
                        st.cache_data.clear()
                        time.sleep(1)
                        force_refresh()
                    else:
                        error = safe_json(resp)
                        st.error(f"❌ {error.get('detail', 'Ошибка')}")
            with col_btn3:
                if st.button("🔄 Обновить"):
                    st.cache_data.clear()
                    force_refresh()
            
            st.divider()
            
            # Отправка сообщения
            with st.form("message_form"):
                msg_text = st.text_input("Сообщение")
                if st.form_submit_button("📨 Отправить"):
                    if msg_text:
                        resp = requests.post(
                            f"{API_URL}/messages",
                            json={
                                "queue_id": selected_queue['q_id'],
                                "user_id": st.session_state.user_id,
                                "text": msg_text
                            },
                            headers=headers
                        )
                        if resp.status_code == 200:
                            st.success("✅ Сообщение отправлено!")
                            time.sleep(0.5)
                            force_refresh()
                        else:
                            error = safe_json(resp)
                            st.error(f"❌ {error.get('detail', 'Ошибка')}")
            
            # Сообщения чата
            st.write("**История сообщений:**")
            
            resp = requests.get(f"{API_URL}/queues/{selected_queue['q_id']}/messages", headers=headers)
            if resp.status_code == 200:
                messages = resp.json()
                if not messages:
                    st.info("💭 Нет сообщений")
                else:
                    for msg in messages:
                        with st.chat_message("user" if msg['user_id'] == st.session_state.user_id else "assistant"):
                            st.markdown(f"**{msg['user_name']}**  `{msg['time']}`")
                            st.write(msg['text'])
            else:
                error = safe_json(resp)
                st.error(f"Ошибка: {error.get('detail', 'Не удалось загрузить сообщения')}")