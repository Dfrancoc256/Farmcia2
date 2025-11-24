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


-- ========================================================
-- 🧩 INSERTAR USUARIO ADMIN
-- ========================================================
INSERT INTO public.usuarios (username, password_hash, rol, activo)
VALUES ('admin', 'admin', 'Administrador', TRUE);


-- ========================================================
-- 🧩 INSERTAR PRODUCTOS
-- ========================================================
INSERT INTO public.productos (nombre, detalle, precio_compra, precio_venta_unidad,
                           precio_venta_blister, unidades_por_blister, stock_unidades, categoria)
VALUES
('Ibuprofeno 400mg', 'Caja x 20 tabletas', 8.00, 1.00, 15.00, 20, 200, 'dolor'),
('Panadol Ultra', 'Blister x 10 tabletas', 7.00, 1.00, 9.00, 10, 150, 'dolor'),
('Amoxicilina 500mg', 'Blister x 12 caps', 12.00, 2.00, 20.00, 12, 120, 'antibiótico'),
('Loratadina 10mg', 'Tabletas', 3.00, 0.75, 6.50, 10, 180, 'alergia'),
('Suero Oral 500ml', 'Botella', 4.00, 6.00, NULL, NULL, 90, 'rehidratación'),
('Jarabe Antigripal', 'Frasco 120ml', 10.00, 15.00, NULL, NULL, 50, 'resfrío');


-- ========================================================
-- 🧩 VENTAS EJEMPLO
-- ========================================================
INSERT INTO public.ventas (total, tipo_pago, observacion, id_usuario)
VALUES
(20.00, 'efectivo', 'Venta ejemplo', 1),
(35.00, 'efectivo', 'Venta ejemplo 2', 1);

-- Venta 1
INSERT INTO public.detalle_ventas (id_venta, id_producto, tipo, cantidad, precio_unitario,
                                  unidades_descuento, costo_unitario_compra)
VALUES
(1, 1, 'unidad', 5, 1.00, 5, 8.00/20),
(1, 5, 'unidad', 1, 6.00, 1, 4.00);

-- Venta 2
INSERT INTO public.detalle_ventas (id_venta, id_producto, tipo, cantidad, precio_unitario,
                                  unidades_descuento, costo_unitario_compra)
VALUES
(2, 3, 'blister', 1, 20.00, 12, 12.00/12),
(2, 4, 'unidad', 3, 0.75, 3, 3.00/10);


-- ========================================================
-- 🧩 DESCONTAR STOCK
-- ========================================================
UPDATE public.productos p
SET stock_unidades = p.stock_unidades - dv.unidades_descuento
FROM public.detalle_ventas dv
WHERE p.id = dv.id_producto;


-- ========================================================
-- 🧩 MOV INVENTARIO AUTOMÁTICO
-- ========================================================
INSERT INTO public.movimientos_inventario (id_producto, tipo, cantidad, referencia, motivo, stock_resultante)
SELECT
    dv.id_producto,
    'venta',
    dv.unidades_descuento,
    'V-' || dv.id_venta,
    'Descuento por venta automática',
    p.stock_unidades
FROM public.detalle_ventas dv
JOIN public.productos p ON p.id = dv.id_producto;


-- ========================================================
-- 🧩 FIADOS EJEMPLO
-- ========================================================
INSERT INTO public.fiados (id_producto, nombre_cliente, telefono, producto, cantidad, monto, estado)
VALUES
(1, 'Juan Pérez', '5555-1111', 'Ibuprofeno 400mg', 2, 2.00, 'Pendiente'),
(3, 'María López', '5511-3344', 'Amoxicilina 500mg', 1, 2.00, 'Pagado');

-- ========================================================
-- 🧩 GASTOS EJEMPLO
-- ========================================================
INSERT INTO public.gastos (descripcion, monto, categoria)
VALUES
('Compra de sueros', 150.00, 'mercadería'),
('Pago de luz', 220.00, 'servicios'),
('Publicidad en Facebook', 80.00, 'marketing');
