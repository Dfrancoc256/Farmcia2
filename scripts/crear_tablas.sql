-- ==============================================
-- 🧱 FARMACIA 2.0 - POSTGRESQL / SUPABASE
-- ==============================================

-- 1) Crear esquema si no existe
CREATE SCHEMA IF NOT EXISTS public;

-- ========================================================
-- 🧩 TABLA: USUARIOS
-- ========================================================
CREATE TABLE public.usuarios (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    rol TEXT NOT NULL CHECK (rol IN ('Administrador', 'Cajero', 'Invitado')),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ========================================================
-- 🧩 TABLA: PRODUCTOS
-- ========================================================
CREATE TABLE public.productos (
    id BIGSERIAL PRIMARY KEY,
    codigo TEXT GENERATED ALWAYS AS ('P' || LPAD(id::text, 5,'0')) STORED,
    nombre TEXT NOT NULL,
    detalle TEXT,
    precio_compra NUMERIC(10,2) NOT NULL,
    precio_venta_unidad NUMERIC(10,2) NOT NULL,
    precio_venta_blister NUMERIC(10,2),
    unidades_por_blister INT,
    stock_unidades INT NOT NULL DEFAULT 0,
    stock_actual INT NOT NULL DEFAULT 0,
    categoria TEXT,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_registro TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ========================================================
-- 🧩 TABLA: VENTAS
-- ========================================================
CREATE TABLE public.ventas (
    id BIGSERIAL PRIMARY KEY,
    fecha TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    total NUMERIC(10,2) NOT NULL,
    tipo_pago TEXT,
    observacion TEXT,
    id_usuario BIGINT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'Activa',
    FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id)
);

-- ========================================================
-- 🧩 TABLA: DETALLE_VENTAS
-- ========================================================
CREATE TABLE public.detalle_ventas (
    id BIGSERIAL PRIMARY KEY,
    id_venta BIGINT NOT NULL,
    id_producto BIGINT NOT NULL,
    tipo TEXT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario NUMERIC(10,2) NOT NULL,
    unidades_descuento INT NOT NULL,
    costo_unitario_compra NUMERIC(10,2) NOT NULL,
    subtotal NUMERIC GENERATED ALWAYS AS (cantidad * precio_unitario) STORED,
    FOREIGN KEY (id_venta) REFERENCES public.ventas(id),
    FOREIGN KEY (id_producto) REFERENCES public.productos(id)
);

-- ========================================================
-- 🧩 TABLA: FIADOS
-- ========================================================
CREATE TABLE public.fiados (
    id BIGSERIAL PRIMARY KEY,
    id_producto BIGINT NOT NULL,
    nombre_cliente TEXT NOT NULL,
    telefono TEXT,
    producto TEXT,
    cantidad INT NOT NULL,
    monto NUMERIC(10,2) NOT NULL,
    fecha TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    estado TEXT NOT NULL DEFAULT 'Pendiente',
    fecha_pago TIMESTAMPTZ,
    id_venta BIGINT,
    FOREIGN KEY (id_producto) REFERENCES public.productos(id),
    FOREIGN KEY (id_venta) REFERENCES public.ventas(id)
);

-- ========================================================
-- 🧩 TABLA: GASTOS
-- ========================================================
CREATE TABLE public.gastos (
    id BIGSERIAL PRIMARY KEY,
    descripcion TEXT NOT NULL,
    monto NUMERIC(10,2) NOT NULL,
    fecha TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    categoria TEXT
);

-- ========================================================
-- 🧩 TABLA: MOV INVENTARIO
-- ========================================================
CREATE TABLE public.movimientos_inventario (
    id BIGSERIAL PRIMARY KEY,
    id_producto BIGINT NOT NULL,
    tipo TEXT NOT NULL,
    cantidad INT NOT NULL,
    referencia TEXT,
    motivo TEXT,
    fecha TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    stock_resultante INT NOT NULL,
    FOREIGN KEY (id_producto) REFERENCES public.productos(id)
);


