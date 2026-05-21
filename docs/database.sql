-- =========================================================================
-- PROYECTO TFG DAW: CaterChef Fusión
-- SCRIPT DE ESTRUCTURA DE BASE DE DATOS (POSTGRESQL)
-- =========================================================================

-- 1. LIMPIEZA DE TABLAS EXISTENTES (Evita conflictos al reimportar)
DROP TABLE IF EXISTS "detalles_pedido" CASCADE;
DROP TABLE IF EXISTS "lista_espera" CASCADE;
DROP TABLE IF EXISTS "pedidos" CASCADE;
DROP TABLE IF EXISTS "reservas_chef" CASCADE;
DROP TABLE IF EXISTS "usuarios" CASCADE;
DROP TABLE IF EXISTS "platos" CASCADE;

-- 2. CREACIÓN DE TABLAS MAESTRAS (No dependen de ninguna otra)
CREATE TABLE "platos" (
	"id" serial PRIMARY KEY,
	"nombre" varchar(150) NOT NULL,
	"descripcion" text,
	"precio" numeric(10, 2) NOT NULL,
	"categoria" varchar(100),
	"imagen_url" varchar(500),
	"alergenos" varchar(255),
	"disponible" boolean DEFAULT true,
	"creado_en" timestamp DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "usuarios" (
	"id" serial PRIMARY KEY,
	"nombre" varchar(100) NOT NULL,
	"apellidos" varchar(150),
	"email" varchar(255) NOT NULL CONSTRAINT "usuarios_email_key" UNIQUE,
	"password_hash" varchar(255) NOT NULL,
	"rol" varchar(50) DEFAULT 'cliente',
	"activo" boolean DEFAULT true,
	"creado_en" timestamp DEFAULT CURRENT_TIMESTAMP,
	"telefono" varchar(20),
	"acepta_privacidad" boolean DEFAULT false
);

CREATE TABLE "reservas_chef" (
	"id" serial PRIMARY KEY,
	"nombre" varchar(150) NOT NULL,
	"email" varchar(255) NOT NULL,
	"fecha" date NOT NULL,
	"tipo_evento" varchar(100) NOT NULL,
	"tipo_chef" varchar(100) NOT NULL,
	"comensales" integer NOT NULL,
	"fecha_solicitud" timestamp DEFAULT CURRENT_TIMESTAMP
);

-- 3. CREACIÓN DE TABLAS TRANSACCIONALES (Dependen de las tablas maestras)
CREATE TABLE "lista_espera" (
	"id" serial PRIMARY KEY,
	"plato_id" integer,
	"email_usuario" varchar(255) NOT NULL,
	"fecha_solicitud" timestamp DEFAULT CURRENT_TIMESTAMP,
	"estado" varchar(20) DEFAULT 'pendiente'
);

CREATE TABLE "pedidos" (
	"id" serial PRIMARY KEY,
	"usuario_id" integer,
	"tipo_servicio" varchar(50) NOT NULL,
	"fecha_servicio" timestamp NOT NULL,
	"estado" varchar(50) DEFAULT 'pendiente_pago',
	"total" numeric(10, 2) DEFAULT '0.00' NOT NULL,
	"direccion_calle" varchar(255) NOT NULL,
	"ciudad" varchar(100) NOT NULL,
	"codigo_postal" varchar(10) NOT NULL,
	"provincia" varchar(50) NOT NULL,
	"notas_cliente" text,
	"creado_en" timestamp DEFAULT CURRENT_TIMESTAMP,
	"distrito" varchar(100),
	"telefono" varchar(20),
	CONSTRAINT "pedidos_provincia_check" CHECK (((provincia)::text = ANY ((ARRAY['Madrid'::character varying, 'Toledo'::character varying])::text[])))
);

CREATE TABLE "detalles_pedido" (
	"id" serial PRIMARY KEY,
	"pedido_id" integer,
	"plato_id" integer,
	"cantidad" integer NOT NULL,
	"precio_unitario" numeric(10, 2) NOT NULL,
	"subtotal" numeric(10, 2) GENERATED ALWAYS AS (((cantidad)::numeric * precio_unitario)) STORED,
	CONSTRAINT "detalles_pedido_cantidad_check" CHECK ((cantidad > 0))
);

-- 4. RESTRICCIONES DE CLAVES FORÁNEAS (Garantizan la integridad referencial [cite: 17])
ALTER TABLE "detalles_pedido" ADD CONSTRAINT "detalles_pedido_pedido_id_fkey" FOREIGN KEY ("pedido_id") REFERENCES "pedidos"("id") ON DELETE CASCADE;
ALTER TABLE "detalles_pedido" ADD CONSTRAINT "detalles_pedido_plato_id_fkey" FOREIGN KEY ("plato_id") REFERENCES "platos"("id") ON DELETE RESTRICT;
ALTER TABLE "lista_espera" ADD CONSTRAINT "lista_espera_plato_id_fkey" FOREIGN KEY ("plato_id") REFERENCES "platos"("id") ON DELETE CASCADE;
ALTER TABLE "pedidos" ADD CONSTRAINT "pedidos_usuario_id_fkey" FOREIGN KEY ("usuario_id") REFERENCES "usuarios"("id") ON DELETE CASCADE;

-- =========================================================================
-- 5. INSERCIÓN DE DATOS SEMILLA (Menú Oficial Fusión y Usuarios de Control)
-- =========================================================================

-- 5.1 CATÁLOGO DE PLATOS OFICIALES (Mapeados exactamente con tu Neon DB)
INSERT INTO "platos" ("id", "nombre", "descripcion", "precio", "categoria", "imagen_url", "alergenos", "disponible", "creado_en") VALUES 
(1, 'Ceviche de Corvina con reducción de Sidra', 'Corvina fresca marinada en lima, ají limo y un toque sutil de reducción de sidra asturiana.', 18.50, 'Entrante', NULL, 'Pescado', true, '2026-05-19 16:35:55'),
(2, 'Croquetas cremosas de Ají de Gallina', 'Tradicional masa de croqueta española rellena del guiso peruano de ají de gallina, pecanas y queso.', 12.00, 'Entrante', NULL, 'Gluten, Lácteos, Frutos Secos', true, '2026-05-19 16:35:55'),
(3, 'Lomo Saltado al estilo Madrileño', 'Tiras de solomillo salteadas al wok con cebolla, tomate, ají amarillo, acompañadas de patatas bravas.', 22.00, 'Principal', NULL, 'Soja, Gluten', false, '2026-05-19 16:35:55'),
(4, 'Causa Rellena de Pulpo a la Gallega', 'Base de patata prensada con ají amarillo y limón, coronada con pulpo laminado, pimentón de la Vera y aceite de oliva.', 16.50, 'Entrante', NULL, 'Moluscos', true, '2026-05-19 16:35:55'),
(5, 'Suspiro de Limeña', 'Clásico postre peruano a base de manjar blanco y yemas, coronado con merengue al oporto y canela.', 6.50, 'Postre', NULL, 'Lácteos, Huevos', true, '2026-05-20 01:10:04'),
(6, 'Tarta de Queso Fluida', 'Tarta de queso al horno estilo viña, con un toque de lúcuma y base de galleta artesanal.', 7.00, 'Postre', NULL, 'Gluten, Lácteos, Huevos', true, '2026-05-20 01:10:04');

-- Ajustar el secuenciador de la clave primaria de platos para que no choque en futuros INSERTs
SELECT setval('platos_id_seq', (SELECT MAX(id) FROM platos));


-- 5.2 CUENTAS DE USUARIO DE CONTROL (Estructura real con contraseñas hasheadas en Bcrypt)
INSERT INTO "usuarios" ("id", "nombre", "apellidos", "email", "password_hash", "rol", "activo", "telefono", "acepta_privacidad", "creado_en") VALUES 
(1, 'Carlos Alberto', 'Campos', 'campos@gmail.com', '$2b$12$LhEh83PnJTiNWWLGC.IuOu893lnyRfZV3oPlh6UfOY3t09nNGecl6', 'admin', true, '699777444', false, '2026-05-20 08:53:02'),
(2, 'Julia', 'Castillo', 'castillo@gmail.com', '$2b$12$hmRUNgibV3LhDP/EEq9moOfHLjaWKi80fCCAFF8FUeEZvnb/gtDrS', 'cliente', true, '600111222', false, '2026-05-20 11:32:35');

-- Ajustar el secuenciador de la clave primaria de usuarios
SELECT setval('usuarios_id_seq', (SELECT MAX(id) FROM usuarios));