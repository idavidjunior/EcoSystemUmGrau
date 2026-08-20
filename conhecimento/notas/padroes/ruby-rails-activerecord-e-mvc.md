---
tags: [auto, padrao, ruby, timestamps, update, updated]
aliases: [Ruby: Rails — ActiveRecord e MVC]
date: 2026-08-20
---

# Ruby: Rails — ActiveRecord e MVC

**Fonte:** ruby

### Convenção sobre configuração

Rails (Ruby on Rails) organiza o MVC em pastas fixas: `app/models`, `app/controllers`, `app/views`, `config/routes.rb`. Convenções que economizam configuração: tabela é o plural snake_case do modelo (`User` → `users`), PK `id` (bigint auto), FK `<modelo>_id`, timestamps `created_at`/`updated_at`. Migrações em `db/migrate` versionam o schema (DDL como código, reversível via `down`).

### ActiveRecord (ORM)

- **Query interface**: `User.where(active: true).order(:name).limit(10).offset(20)` — **lazy**, só executa SQL ao materializar (`.to_a`, `.first`, `.count`, `.each`, `.exists?`). A relação é encadeável e imutável em relação às cláusulas originais.
- **Associations**: `has_many`, `belongs_to`, `has_one`, `has_and_belongs_to_many`, `has_many through:`. Configure `dependent: :destroy` / `:nullify` para integridade no delete.
- **N+1 problem**: `users.each { |u| u.posts }` dispara 1+N queries. Corrija com `includes(:posts)` (eager load); `preload`/`eager_load` controlam a estratégia de join.
- **Validations** no modelo: `validates :email, presence: true, uniqueness: true`. `save` retorna `false` se inválido; `save!` levanta `RecordInvalid`. Use `errors` para mensagens.
- **Callbacks**: `before_save`, `after_create`, `after_commit` — use com parcimônia; efeitos colaterais ocultos dificultam testes. Para fluxos complexos, service objects.

### Controllers e rotas

`resources :posts` gera as 7 rotas REST (index/show/new/create/edit/update/destroy). O controller responde com `render`/`redirect_to`; parâmetros passam por **Strong Parameters**: `params.require(:post).permit(:title, :body)`. Views em ERB/Slim: apresentação apenas.

### MVC na prática

Controller fino, model gordo, view burra. Regras de negócio em modelos/service objects; consultas agregadas em `scope`s reutilizáveis.

```ruby
class Post < ApplicationRecord
  belongs_to :user
  validates :title, presence: true
  scope :published, -> { where(published: true) }
end

# Controller
@posts = Post.published.includes(:user).order(created_at: :desc)
```
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[ruby-blocks-procs-e-lambdas]]
- [[ruby-tudo-é-objeto-e-duck-typing]]