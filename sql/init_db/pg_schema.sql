--
-- Таблица для Telegram-Bot 
--

CREATE table if not exists public.object_states (
	istateid int2 NOT NULL,
	vcname text NOT NULL,
	CONSTRAINT object_states_pkey PRIMARY KEY (istateid)
);

insert into public.object_states (istateid,vcname)
values (1, 'Черновик'),
(100, 'Опубликован'),
(101, 'Авторизация не пройдена');

-- схема модуля

CREATE SCHEMA if not exists rtb;

SET search_path = rtb;

create sequence account_seq;
create sequence question_seq;
create sequence answer_seq;
create sequence question_map_seq;
create sequence account_chat_seq;

-- таблица пользователей, для которых открыт доступ
CREATE TABLE account (
  iaccountid  integer       not null default nextval('account_seq'),
  vcphone     varchar(100)  not null,                                   -- Номер телефона
  vcname      varchar(255)  not null,                                   -- Имя
  itgid        integer       null,                                       -- Идентификатор пользователя в Телеграме
  bactive     boolean       not null default true,                      -- признак активности
  constraint account_pkey primary key (iaccountid),
  constraint account_phone_ukey unique (vcphone)                        -- чтоб не было дублей по номерам телефона
);

-- таблица типов вопросов
-- определеяет какой ожидается формат ответа на вопрос
CREATE TABLE question_type (
  itypeid   smallint  not null,
  vctitle   text      not null,
  constraint question_type_pkey primary key (itypeid)
);

-- таблица вопросов
CREATE TABLE question (
  iquestionid  integer  not null default nextval('question_seq'),
  vctitle      text     not null,                                       -- Текст вопроса
  itypeid      smallint  not null,
  keyboard_orientation varchar(20),
  constraint question_pkey primary key (iquestionid),
  constraint question_type_fkey foreign key (itypeid)
    references question_type (itypeid) on delete restrict on update restrict
);

-- таблица вариантов ответов на вопрос
CREATE TABLE answer (
  ianswerid    integer  not null default nextval('answer_seq'),
  iquestionid  integer  not null,                                       -- ID вопроса
  vctitle      text     not null,                                       -- Текст варианта ответа
  constraint answer_pkey primary key (ianswerid),
  constraint answer_question_fkey foreign key (iquestionid)
    references question (iquestionid) on delete cascade on update restrict
);



-- таблица карты вопросов
-- определяет последовательность задавания вопросов
CREATE TABLE question_map (
  imapid            integer  not null default nextval('question_map_seq'),
  iprev_questionid  integer  null,
  inext_questionid  integer  null,
  ianswerid         integer  null,
  constraint question_map_pkey primary key (imapid),
  constraint map_prev_question_fkey foreign key (iprev_questionid)
    references question (iquestionid) on delete cascade on update restrict,
  constraint map_next_question_fkey foreign key (inext_questionid)
    references question (iquestionid) on delete cascade on update restrict,
  constraint map_answer_fkey foreign key (ianswerid)
    references answer (ianswerid) on delete cascade on update restrict
);

-- анализ данных в карте. проверка валидности
create or replace function question_map_func() returns trigger as $$
begin
    if NEW.iprev_questionid is null and NEW.inext_questionid is null THEN
        -- недопустимо. сгенерим ошибку
        raise 'cannot previous and next question is null';
    END IF;
    -- при отсудствии ID предыдущего вопроса, ID ответа быть не может
    if NEW.iprev_questionid is null and NEW.ianswerid is not null THEN
        -- недопустимо. сгенерим ошибку
        raise 'cannot set answer if empty previous question';
    END IF;
    -- проверим есть ли предуыдущий шаг, который приводить к текущему
    if NEW.iprev_questionid is not null and not exists(select 1 from rtb.question_map where inext_questionid=NEW.iprev_questionid) THEN
        raise 'cannot find previous step (id %)', NEW.iprev_questionid;
    END IF;
    -- проверим принадлежил ли ответ заданному предыдущему вопросу
    if NEW.iprev_questionid is not null and NEW.ianswerid is not null and not exists(select 1 from rtb.answer where ianswerid=NEW.ianswerid and iquestionid=NEW.iprev_questionid) THEN
        -- левый вопрос, генерим ошибку
        raise 'cannot find variant of answer (id %) in question (id %)', NEW.ianswerid, NEW.iprev_questionid;
    END IF;
    -- проверки прошли. можно сохранить
    return NEW;
end;
$$ language plpgsql;

create trigger question_map_trigger
  before insert or update on question_map
  for each row execute procedure question_map_func();

-- таблица чата пользователя
CREATE TABLE account_chat (
  ichatid     integer   not null default nextval('account_chat_seq'),
  iaccountid  integer   not null,                                     -- ID пользователя
  dtstart     timestamp(0) with time zone not null default now(),     -- Дата начала диалога (создается по команде /start)
  istateid    smallint  not null,                                     -- статус диалога (1 - черновик, 100 - опубликован, 101 - Авторизация не пройдена)
  constraint account_chat_pkey primary key (ichatid),
  constraint account_chat_account_fkey foreign key (iaccountid)
    references account (iaccountid) on delete restrict on update restrict,
  constraint account_chat_states_fkey foreign key (istateid)
    references public.object_states (istateid) on delete restrict on update restrict
);


-- таблица ответов в чате пользователя
CREATE TABLE account_chat_answer (
	ichatid integer NOT NULL,
	iquestionid integer NOT NULL,
	ianswerid integer NULL,
	vcanswer text NULL,
  --constraint account_chat_answer_pkey primary key (ichatid, iquestionid,ianswerid), --,
  --constraint account_chat_answer_check check ((ianswerid is null and vcanswer is not null) or (ianswerid is not null and vcanswer is null)),
  constraint account_chat_answer_question_fkey foreign key (iquestionid)
    references question(iquestionid) on delete cascade on update restrict,
  constraint account_chat_answer_fkey foreign key (ianswerid)
    references answer(ianswerid) on delete cascade on update restrict
);

--drop function rtb.account_chat_answer_func() cascade

-- функция проверки данных ответов на вопросы
create or replace function account_chat_answer_func() returns trigger as $$
begin
  -- проверим что ответ относиться к вопросу
  if NEW.ianswerid is not null and not exists(select 1 from rtb.answer where ianswerid=NEW.ianswerid and iquestionid=NEW.iquestionid) THEN
    -- недопустимо. сгенерим ошибку
      raise 'cannot find variant of answer (id %) in question (id %)', NEW.ianswerid, NEW.iquestionid;
  END IF;
  -- если задан вариант ответа. затрем текст, он по идее не нужен
  if NEW.ianswerid is not null THEN
      NEW.vcanswer = null;
  END IF;
  -- проверки прошли. можно сохранить
  return NEW;
end;
$$ language plpgsql;

create trigger account_chat_answer_trigger
  before insert or update on rtb.account_chat_answer
  for each row execute procedure account_chat_answer_func();
  
 
INSERT INTO rtb.question_type
(itypeid, vctitle)
VALUES(1, 'text');
INSERT INTO rtb.question_type
(itypeid, vctitle)
VALUES(2, 'name');
INSERT INTO rtb.question_type
(itypeid, vctitle)
VALUES(3, 'attach');
INSERT INTO rtb.question_type
(itypeid, vctitle)
VALUES(4, 'time');
INSERT INTO rtb.question_type
(itypeid, vctitle)
VALUES(5, 'text+data');
INSERT INTO rtb.question_type
(itypeid, vctitle)
VALUES(6, 'text+geo');
INSERT INTO rtb.question_type
(itypeid, vctitle)
VALUES(7, 'contact');
INSERT INTO rtb.question_type
(itypeid, vctitle)
VALUES(8, 'text+contact');

insert into rtb.account (vcphone,vcname,itgid,bactive)
values ('79287769434','Романченко Родион',477068727,True);


--delete from rtb.question; 
--delete from rtb.answer ;
--delete from rtb.question_map ;

INSERT INTO rtb.question(
	iquestionid, vctitle, itypeid)
	VALUES (1, 'Введите номер телефона', 2),
			--(2,'Как к вам можно обращаться?',1),
			(3,'Какой источник данных интересует?',1),
			(4,'Каким способом хотите получить данные?',1), -- Matomo
			(5,'Каким способом хотите получить данные?',1), -- Logs
			(6,'Выберите шаблон',1), -- Matomo
			(7,'Выберите шаблон',1); -- Logs
			--(8,'Выберите шаблон',1), 
			
--			(5,'Жалобы на какую услугу',1),
--			(6,'Укажите симптомы',1),
--			(7,'Укажите симптомы',1),
--			(8,'Укажите номер абонента Б',2),
--			(9,'Укажите технологию (2G, 3G, 4G)',1),
--			(10,'Укажите технологию (2G, 3G, 4G)',1),
--			(11,'Добавьте вложения или скриншоты',1),
--			(12,'Подтвердить заявку?',1);

			
			
INSERT INTO rtb.answer(
	ianswerid, iquestionid, vctitle)
	VALUES (1, 1, 'Указать свой номер'),
			--(2, 2, 'Указать свое имя'),
			(3, 3, 'Измерения Matomo'),
			(4, 3, 'Логи веб-приложения'),
			(5, 4, 'Выгрузка по шаблону'),	--Matomo
			(6, 4, 'Сформировать запрос'),	--Matomo
			(7, 5, 'Выгрузка по шаблону'),	--Logs
			(8, 5, 'Сформировать запрос'),	--Logs
			(9, 6,'Визиты'),				--Matomo
			(10, 6, 'Устройства'),          --Matomo
			(11, 6, 'Пользователи'),		--Matomo
			(12, 6, 'Карта'),				--Matomo
			(13, 6, 'Закончить'),			--Matomo
			(14, 7, 'Статусы'),
			(15, 7, 'Ошибки'),
			(16, 7, 'Предупреждения'),
			(17, 7, 'Запросы'),
			(18, 7, 'Закончить');			--Logs
			--(13, )
			
--			(9, 6, 'Тишина'),
--			(10, 6, 'Обрыв'),
--			(11, 6, 'Недозвон'),
--			(12, 6, 'Низкое качество речи'),
--			(13, 7, 'Низкая скорость'),
--			(14, 8, 'Добавить из контактов'),
--			(15, 9, '2G'),
--			(16, 9, '3G'),
--			(17, 9, '4G'),
--			(18, 10, '2G'),
--			(19, 10, '3G'),
--			(20, 10, '4G'),
--			(21, 12, 'Да'),
--			(22, 12, 'Нет');

		
INSERT INTO rtb.question_map(
	iprev_questionid, inext_questionid, ianswerid)
	VALUES (null, 1, null),
			(1, 3, null),
			--(2, 3, null),
			(3, 4, 3),
			(3, 5, 4),
			(4, 6, 5),
			(5, 7, 7),
			(6, 6, 9),
			(6, 6, 10),
			(6, 6, 11),
			(6, 6, 12),
			(6,null,13),
			(7,7,14),
			(7,7,15),
			(7,7,16),
			(7,7,17),
			(7,null,18);

--select * from answer a 
		
--select * from account a 
		
--select * from account_chat

--select * from account_chat_answer

--delete from account_chat_answer

--INSERT INTO rtb.account_chat_answer
--    	        (ichatid, iquestionid, ianswerid, vcanswer)
--    	            VALUES (32, 3, 4, 'Логи веб-приложения');

--INSERT INTO rtb.question_map(
--	iprev_questionid, inext_questionid, ianswerid)
--	VALUES
--			(7, 9, null);
--INSERT INTO rtb.question_map(
--	iprev_questionid, inext_questionid, ianswerid)
--	VALUES
--			(8, 11, null);
--INSERT INTO rtb.question_map(
--	iprev_questionid, inext_questionid, ianswerid)
--	VALUES
--			(9, 11, null);
--INSERT INTO rtb.question_map(
--	iprev_questionid, inext_questionid, ianswerid)
--	VALUES
--			(10, 11, null);
--INSERT INTO rtb.question_map(
--	iprev_questionid, inext_questionid, ianswerid)
--	VALUES			
--			(11, 12, null);
--INSERT INTO rtb.question_map(
--	iprev_questionid, inext_questionid, ianswerid)
--	VALUES			
--			(12, null, 21);
----select * from rtb.account_chat

--INSERT INTO rtb.question(
--	iquestionid, vctitle, itypeid)
--	VALUES (1, 'Введите номер телефона', 2),
--			(2,'Как к вам можно обращаться?',1),
--			(3,'',1),
--			(4,'Укажите почтовый адрес, где возникла проблема',4),
--			(5,'Жалобы на какую услугу',1),
--			(6,'Укажите симптомы',1),
--			(7,'Укажите симптомы',1),
--			(8,'Укажите номер абонента Б',2),
--			(9,'Укажите технологию (2G, 3G, 4G)',1),
--			(10,'Укажите технологию (2G, 3G, 4G)',1),
--			(11,'Добавьте вложения или скриншоты',1),
--			(12,'Подтвердить заявку?',1);