-- =========================================================================
-- PROYECTO TFG DAW: CaterChef Fusión
-- SCRIPT DE ESTRUCTURA DE BASE DE DATOS (POSTGRESQL) - ACTUALIZADO
-- =========================================================================

-- 1. LIMPIEZA DE TABLAS
DROP TABLE IF EXISTS "detalles_pedido" CASCADE;
DROP TABLE IF EXISTS "lista_espera" CASCADE;
DROP TABLE IF EXISTS "pedidos" CASCADE;
DROP TABLE IF EXISTS "reservas_chef" CASCADE;
DROP TABLE IF EXISTS "usuarios" CASCADE;
DROP TABLE IF EXISTS "platos" CASCADE;
DROP TABLE IF EXISTS "mensajes_contacto" CASCADE;

-- 2. CREACIÓN DE TABLAS MAESTRAS
CREATE TABLE "platos" (
    "id" serial PRIMARY KEY,
    "nombre" varchar(150) NOT NULL,
    "descripcion" text,
    "precio" numeric(10, 2) NOT NULL,
    "categoria" varchar(100),
    "imagen_url" varchar(500), -- Nombre del archivo de imagen
    "alergenos" varchar(255),
    "disponible" boolean DEFAULT true,
    "creado_en" timestamp DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "usuarios" (
    "id" serial PRIMARY KEY,
    "nombre" varchar(100) NOT NULL,
    "apellidos" varchar(150),
    "email" varchar(255) NOT NULL UNIQUE,
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

-- 3. CREACIÓN DE TABLAS TRANSACCIONALES
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
    -- Campos para Checkout de Invitados
    "nombre_invitado" varchar(100),
    "apellidos_invitado" varchar(100),
    "email_invitado" varchar(150),
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

CREATE TABLE "mensajes_contacto" (
    "id" serial PRIMARY KEY,
    "nombre" varchar(100) NOT NULL,
    "email" varchar(255) NOT NULL,
    "telefono" varchar(20),
    "numero_pedido" varchar(50),
    "tipo_evento" varchar(100),
    "mensaje" text NOT NULL,
    "leido" boolean DEFAULT false,
    "acepta_privacidad" boolean NOT NULL DEFAULT false,
    "acepta_comerciales" boolean DEFAULT false,
    "creado_en" timestamp DEFAULT CURRENT_TIMESTAMP
);

-- 4. RESTRICCIONES DE CLAVES FORÁNEAS
ALTER TABLE "detalles_pedido" ADD CONSTRAINT "detalles_pedido_pedido_id_fkey" FOREIGN KEY ("pedido_id") REFERENCES "pedidos"("id") ON DELETE CASCADE;
ALTER TABLE "detalles_pedido" ADD CONSTRAINT "detalles_pedido_plato_id_fkey" FOREIGN KEY ("plato_id") REFERENCES "platos"("id") ON DELETE RESTRICT;
ALTER TABLE "lista_espera" ADD CONSTRAINT "lista_espera_plato_id_fkey" FOREIGN KEY ("plato_id") REFERENCES "platos"("id") ON DELETE CASCADE;
ALTER TABLE "pedidos" ADD CONSTRAINT "pedidos_usuario_id_fkey" FOREIGN KEY ("usuario_id") REFERENCES "usuarios"("id") ON DELETE CASCADE;

-- 5. INSERCIÓN DE DATOS SEMILLA
-- He asignado el nombre de archivo correspondiente a cada plato según nuestra lista
INSERT INTO "platos" ("id", "nombre", "descripcion", "precio", "categoria", "imagen_url", "alergenos", "disponible") VALUES 
(1, 'Ceviche de Corvina con reducción de Sidra', 'Corvina marinada en lima, ají limo y sidra.', 18.50, 'Entrante', 'ceviche-corvina-sidra.png', 'Pescado', true),
(2, 'Croquetas cremosas de Ají de Gallina', 'Tradicional masa con guiso peruano, pecanas y queso.', 12.00, 'Entrante', 'croquetas-aji-gallina.png', 'Gluten, Lácteos', true),
(3, 'Lomo Saltado al estilo Madrileño', 'Ternera salteada con toque de ají y patatas bravas.', 22.00, 'Principal', 'lomo-saltado-madrileno.png', 'Soja, Gluten', false),
(4, 'Causa Rellena de Pulpo', 'Patata con ají amarillo y pulpo al pimentón.', 16.50, 'Entrante', 'causa-pulpo-gallega.png', 'Moluscos', true),
(5, 'Suspiro de Limeña', 'Manjar blanco, merengue al oporto y canela.', 6.50, 'Postre', 'suspiro-limena.png', 'Lácteos, Huevos', true),
(6, 'Tarta de Queso Fluida', 'Estilo viña con lúcuma y galleta artesana.', 7.00, 'Postre', 'tarta-queso-fluida.png', 'Gluten, Lácteos', true),
(7, 'Ceviche Clásico Carretillero', 'Pescado fresco, leche de tigre y camote glaseado.', 17.00, 'Entrante', 'ceviche-clasico-carretillero.png', 'Pescado', true),
(8, 'Papa a la Huancaína', 'Patatas en crema de ají amarillo y queso.', 9.50, 'Entrante', 'papa-huancaina.webp', 'Lácteos', true),
(9, 'Seco de Cordero', 'Cordero al cilantro con arroz y frijoles.', 21.00, 'Principal', 'seco-cordero-frijoles.jpg', 'Ninguno', true),
(10, 'Ají de Gallina Clásico', 'Pechuga en crema de ají amarillo con nueces.', 18.00, 'Principal', 'aji-gallina-clasico.jpg', 'Lácteos, Gluten', true),
(11, 'Alfajores de Maicena', 'Galletas de maicena rellenas de manjar.', 5.50, 'Postre', 'alfajores-maicena.jpg', 'Gluten, Lácteos', true),
(12, 'Picarones con Miel', 'Aros de masa frita con almíbar especiado.', 6.00, 'Postre', 'picarones-miel.jpg', 'Gluten', true),
(13, 'Tabla de Ibéricos', 'Jamón de bellota y queso manchego.', 24.00, 'Entrante', 'tabla-ibericos.jpg', 'Lácteos, Gluten', true),
(14, 'Salmorejo Cordobés', 'Tomate, pan de telera y virutas de jamón.', 8.50, 'Entrante', 'salmorejo-cordobes.jpg', 'Gluten, Huevos', true),
(15, 'Paella Valenciana', 'Arroz, pollo, conejo y verdura.', 20.00, 'Principal', 'paella-valenciana.jpg', 'Ninguno', true),
(16, 'Rabo de Toro Estofado', 'Guiso tierno de rabo al vino tinto.', 23.00, 'Principal', 'rabo-toro-estofado.webp', 'Sulfitos', true),
(17, 'Tarta de Santiago', 'Almendras y azúcar glass.', 6.50, 'Postre', 'tarta-santiago.jpg', 'Huevos, Frutos Secos', true),
(18, 'Crema Catalana', 'Crema aromatizada con costra de azúcar.', 6.00, 'Postre', 'crema-catalana.jpg', 'Lácteos, Huevos', true);

SELECT setval('platos_id_seq', (SELECT MAX(id) FROM platos));

INSERT INTO "usuarios" ("id", "nombre", "apellidos", "email", "password_hash", "rol", "activo", "telefono", "acepta_privacidad") VALUES 
(1, 'Admin', 'CaterChef', 'admin@caterchef.com', '$2b$12$LhEh83PnJTiNWWLGC.IuOu893lnyRfZV3oPlh6UfOY3t09nNGecl6', 'admin', true, '000000000', true);

SELECT setval('usuarios_id_seq', (SELECT MAX(id) FROM usuarios));